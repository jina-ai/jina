(executor)=
# Create Executor

{class}`~jina.Executor` process `DocumentArray` in-place via functions decorated with `@requests`. To create an Executor, you only need to follow three principles:

- An `Executor` should subclass directly from `jina.Executor` class.
- An `Executor` class is a bag of functions with shared state (via `self`); it can contain an arbitrary number of
  functions with arbitrary names.
- Functions decorated by `@requests` will be invoked according to their `on=` endpoint.


## Minimum working example

```python
from jina import Executor, requests


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        print(kwargs)

```

````{tab} Use it in a Flow 

```python
from jina import Executor

f = Flow().add(uses=MyExecutor)

with f:
    f.post(on='/random_work', inputs=Document(), on_done=print)
```

````

````{tab} Use it as-is 

```python
m = MyExecutor()
m.foo()
```

````

## Constructor


### Subclass

Every new executor should be subclass from `jina.Executor`.

You can name your executor class freely.

### `__init__`

No need to implement `__init__` if your `Executor` does not contain initial states.

If your executor has `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
in the body:

```python
from jina import Executor


class MyExecutor(Executor):

    def __init__(self, foo: str, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.foo = foo
```


````{admonition} What is inside kwargs? 
:class: tip
Here, `kwargs` contains `metas` and `requests` (representing the request-to-function mapping) values from the YAML
config and `runtime_args` injected on startup. 

You can access the values of these arguments in `__init__` body via `self.metas`/`self.requests`/`self.runtime_args`, 
or modifying their values before sending to `super().__init__()`.
````

### Passing arguments

When using an Executor in a Flow, there are two ways of passing arguments to its `__init__`.

````{tab} via uses_with

```python
from jina import Flow

f = Flow.add(uses=MyExecutor, uses_with={'foo': 'hello', 'bar': 1})

with f:
  ...
```
````

`````{tab} via predefined YAML

````{dropdown} my-exec.yml
:open:

```yaml
jtype: MyExecutor
with:
  foo: hello
  bar: 1
```
````

````{dropdown} my-flow.py
:open:

```python
from jina import Flow

f = Flow.add(uses='my-exec.yml')

with f:
  ...
```
````


`````


```{hint}

`uses_with` has higher priority than predefined `with` config in YAML. When both presented, `uses_with` is picked up first.

```

## Methods

Methods of `Executor` can be named and wrote freely. 

Only methods that are decorated with `@requests` can be used in a `Flow`.

### Method decorator

You can import `requests` decorator via

```python
from jina import requests
```

`@requests` defines when a function will be invoked in the Flow. It has a keyword `on=` to define the endpoint.

To call an Executor's function, uses `Flow.post(on=..., ...)`. For example, given:

```python
from jina import Executor, Flow, Document, requests


class MyExecutor(Executor):

    @requests(on='/index')
    def foo(self, **kwargs):
        print(f'foo is called: {kwargs}')

    @requests(on='/random_work')
    def bar(self, **kwargs):
        print(f'bar is called: {kwargs}')


f = Flow().add(uses=MyExecutor)

with f:
    f.post(on='/index', inputs=Document(text='index'))
    f.post(on='/random_work', inputs=Document(text='random_work'))
    f.post(on='/blah', inputs=Document(text='blah')) 
```

Then:

- `f.post(on='/index', ...)` will trigger `MyExecutor.foo`;
- `f.post(on='/random_work', ...)` will trigger `MyExecutor.bar`;
- `f.post(on='/blah', ...)` will not trigger any function, as no function is bound to `/blah`;

#### Default binding

A class method decorated with plain `@requests` (without `on=`) is the default handler for all endpoints. That means it
is the fallback handler for endpoints that are not found. `f.post(on='/blah', ...)` will invoke `MyExecutor.foo`

```python
from jina import Executor, requests


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        print(kwargs)

    @requests(on='/index')
    def bar(self, **kwargs):
        print(kwargs)
```

#### Multiple bindings

To bind a method with multiple endpoints, you can use `@requests(on=['/foo', '/bar'])`. This allows
either `f.post(on='/foo', ...)` or `f.post(on='/bar', ...)` to invoke that function.

#### No binding

A class with no `@requests` binding plays no part in the Flow. The request will simply pass through without any
processing.

(executor-method-signature)=

### Method signature

Class method decorated by `@request` follows the signature below:

```python
def foo(docs: DocumentArray,
        parameters: Dict,
        docs_matrix: List[DocumentArray],
        groundtruths: Optional[DocumentArray],
        groundtruths_matrix: List[DocumentArray]) -> Optional[DocumentArray]:
    pass
```

The Executor's method receive the following arguments in order:

| Name | Type | Description  |
| --- | --- | --- |
| `docs`   | `DocumentArray`  | `Request.docs`. When multiple requests are available, it is a concatenation of all `Request.docs` as one `DocumentArray`.  |
| `parameters`  | `Dict`  | `Request.parameters`, given by `Flow.post(..., parameters=)` |
| `docs_matrix`  | `List[DocumentArray]`  | When multiple requests are available, it is a list of all `Request.docs`. On single request, it is `None` |
| `groundtruths`   | `Optional[DocumentArray]`  | `Request.groundtruths`. Same behavior as `docs`  |
| `groundtruths_matrix`  | `List[DocumentArray]`  | Same behavior as `docs_matrix` but on `Request.groundtruths` |

````{admonition} Note
:class: note
Executor's methods not decorated with `@request` do not enjoy these arguments.
````

````{admonition} Note
:class: note
The arguments order is designed as common-usage-first. Not alphabetical order or semantic closeness.
````

````{admonition} Hint
:class: hint
If you don't need some arguments, you can suppress them into `**kwargs`. For example:

```{code-block} python
---
emphasize-lines: 7, 11, 16
---
from jina import Executor, requests


class MyExecutor(Executor):

    @requests
    def foo_using_docs_arg(self, docs, **kwargs):
        print(docs)

    @requests
    def foo_using_docs_parameters_arg(self, docs, parameters, **kwargs):
        print(docs)
        print(parameters)

    @requests
    def foo_using_no_arg(self, **kwargs):
        # the args are suppressed into kwargs
        print(kwargs['docs_matrix'])
```
````

### Method returns

Methods decorated with `@request` can return `DocumentArray`, `DocumentArrayMemmap`, `Dict` or `None`.

- If the return is `None`, then Jina considers all changes happen in-place. The next Executor will receive the updated `docs` modified by the current Executor.
- If the return is `DocumentArray` or `DocumentArrayMemmap`, then the current `docs` field in the `Request` will be overridden by the
  return, which will be forwarded to the next Executor in the Flow.
- If the return is a `Dict`, then `Request.parameters` will be updated by union with the return. The next Executor will receive this updated `Request.parameters`. One can leverage this feature to pass parameters between Executors.

So do I need a return? Most time you don't. Let's see some examples.


#### Embed Documents `blob`

In this example, `encode()` uses some neural network to get the embedding for each `Document.blob`, then assign it
to `Document.embedding`. The whole procedure is in-place and there is no need to return anything.

```python
import numpy as np
from jina import requests, Executor, DocumentArray

from my_model import get_predict_model


class PNEncoder(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = get_predict_model()

    @requests
    def encode(self, docs: DocumentArray, *args, **kwargs) -> None:
        _blob, _docs = docs.traverse_flat(['c']).get_attributes_with_docs('blob')
        embeds = self.model.predict(np.stack(_blob))
        for d, b in zip(_docs, embeds):
            d.embedding = b
```

#### Add Chunks by segmenting Document

In this example, each `Document` is segmented by `get_mesh` and the results are added to `.chunks`. After
that, `.buffer` and `.uri` are removed from each `Document`. In this case, all changes happen in-place and there is no
need to return anything.

```python
from jina import requests, Document, Executor, DocumentArray


class ConvertSegmenter(Executor):

    @requests
    def segment(self, docs: DocumentArray, **kwargs) -> None:
        for d in docs:
            d.load_uri_to_buffer()
            d.chunks = [Document(blob=_r['blob'], tags=_r['tags']) for _r in get_mesh(d.content)]
            d.pop('buffer', 'uri')
```

#### Preserve Document `id` only

In this example, a simple indexer stores incoming `docs` in a `DocumentArray`. Then it recreates a new `DocumentArray`
by preserving only `id` in the original `docs` and dropping all others, as the developer does not want to carry all rich
info over the network. This needs a return.

```{code-block} python
---
emphasize-lines: 14
---
from jina import requests, Document, Executor, DocumentArray


class MyIndexer(Executor):
    """Simple indexer class """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)
        return DocumentArray([Document(id=d.id) for d in docs])
```

#### Pass/change request parameters

In this example, `MyExec2` receives the parameters `{'top_k': 10}` from `MyExec1` when the Flow containing `MyExec1 -> MyExec2` in order. 

```{code-block} python
---
emphasize-lines: 7, 13
---
from jina import requests, Document, Executor

class MyExec1(Executor):

    @requests(on='/index')
    def index(self, **kwargs):
        return {'top_k': 10}

class MyExec2(Executor):

    @requests(on='/index')
    def index(self, parameters, **kwargs):
        self.docs[:int(parameters['top_k']))
```
