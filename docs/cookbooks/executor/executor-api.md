## Executor API

`Executor` process `DocumentArray` in-place via functions decorated with `@requests`.

- An `Executor` should subclass directly from `jina.Executor` class.
- An `Executor` class is a bag of functions with shared state (via `self`); it can contain an arbitrary number of
  functions with arbitrary names.
- Functions decorated by `@requests` will be invoked according to their `on=` endpoint.

### Inheritance

Every new executor should be inherited directly from `jina.Executor`.

You can name your executor class freely.

### `__init__` Constructor

If your executor defines `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
in the body:

```python
from jina import Executor


class MyExecutor(Executor):

    def __init__(self, foo: str, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.foo = foo
```

Here, `kwargs` contains `metas` and `requests` (representing the request-to-function mapping) values from the YAML
config and `runtime_args` injected on startup. Note that you can access their values in `__init__` body via `self.metas`
/`self.requests`/`self.runtime_args`, or modifying their values before sending to `super().__init__()`.

No need to implement `__init__` if your `Executor` does not contain initial states.

### Method naming

`Executor`'s methods can be named freely. Methods that are not decorated with `@requests` are irrelevant to Jina.

### `@requests` decorator

`@requests` defines when a function will be invoked. It has a keyword `on=` to define the endpoint.

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

#### Default binding: `@requests` without `on=`

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

#### Multiple bindings: `@requests(on=[...])`

To bind a method with multiple endpoints, you can use `@requests(on=['/foo', '/bar'])`. This allows
either `f.post(on='/foo', ...)` or `f.post(on='/bar', ...)` to invoke that function.

#### No binding

A class with no `@requests` binding plays no part in the Flow. The request will simply pass through without any
processing.

### Method Signature

Class method decorated by `@request` follows the signature below:

```python
def foo(docs: Optional[DocumentArray],
        parameters: Dict,
        docs_matrix: List[DocumentArray],
        groundtruths: Optional[DocumentArray],
        groundtruths_matrix: List[DocumentArray]) -> Optional[DocumentArray]:
    pass
```

### Method Arguments

The Executor's method receive the following arguments in order:

| Name | Type | Description  |
| --- | --- | --- |
| `docs`   | `Optional[DocumentArray]`  | `Request.docs`. When multiple requests are available, it is a concatenation of all `Request.docs` as one `DocumentArray`. When `DocumentArray` has zero element, then it is `None`.  |
| `parameters`  | `Dict`  | `Request.parameters`, given by `Flow.post(..., parameters=)` |
| `docs_matrix`  | `List[DocumentArray]`  | When multiple requests are available, it is a list of all `Request.docs`. On single request, it is `None` |
| `groundtruths`   | `Optional[DocumentArray]`  | `Request.groundtruths`. Same behavior as `docs`  |
| `groundtruths_matrix`  | `List[DocumentArray]`  | Same behavior as `docs_matrix` but on `Request.groundtruths` |

Note, executor's methods not decorated with `@request` do not enjoy these arguments.

The arguments order is designed as common-usage-first. Not alphabetical order or semantic closeness.

If you don't need some arguments, you can suppress them into `**kwargs`. For example:

```python
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

### Method Returns

Methods decorated with `@request` can return `Optional[DocumentArray]`.

The return is optional. **All changes happen in-place.**

- If the return is not `None`, then the current `docs` field in the `Request` will be overridden by the
  returned `DocumentArray`, which will be forwarded to the next Executor in the Flow.
- If the return is just a shallow copy of `Request.docs`, then nothing happens. This is because the changes are already
  made in-place, there is no point to assign the value.

So do I need a return? No, unless you must create a new `DocumentArray`. Let's see some examples.

#### Example 1: Embed Documents `blob`

In this example, `encode()` uses some neural network to get the embedding for each `Document.blob`, then assign it
to `Document.embedding`. The whole procedure is in-place and there is no need to return anything.

```python
import numpy as np
from jina import requests, Executor, DocumentArray

from pods.pn import get_predict_model


class PNEncoder(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = get_predict_model(ckpt_path='ckpt', num_class=2260)

    @requests
    def encode(self, docs: DocumentArray, *args, **kwargs) -> None:
        _blob, _docs = docs.traverse_flat(['c']).get_attributes_with_docs('blob')
        embeds = self.model.predict(np.stack(_blob))
        for d, b in zip(_docs, embeds):
            d.embedding = b
```

#### Example 2: Add Chunks by Segmenting Document

In this example, each `Document` is segmented by `get_mesh` and the results are added to `.chunks`. After
that, `.buffer` and `.uri` are removed from each `Document`. In this case, all changes happen in-place and there is no
need to return anything.

```python
from jina import requests, Document, Executor, DocumentArray


class ConvertSegmenter(Executor):

    @requests
    def segment(self, docs: DocumentArray, **kwargs) -> None:
        for d in docs:
            d.convert_uri_to_buffer()
            d.chunks = [Document(blob=_r['blob'], tags=_r['tags']) for _r in get_mesh(d.content)]
            d.pop('buffer', 'uri')
```

#### Example 3: Preserve Document `id` Only

In this example, a simple indexer stores incoming `docs` in a `DocumentArray`. Then it recreates a new `DocumentArray`
by preserving only `id` in the original `docs` and dropping all others, as the developer does not want to carry all rich
info over the network. This needs a return.

```python
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

### YAML Interface

An Executor can be loaded from and stored to a YAML file. The YAML file has the following format:

```yaml
jtype: MyExecutor
with:
  ...
metas:
  ...
requests:
  ...
```

- `jtype` is a string. Defines the class name, interchangeable with bang mark `!`;
- `with` is a map. Defines kwargs of the class `__init__` method
- `metas` is a dictionary. It defines the meta information of that class. It contains the following fields:
    - `name` is a string. Defines the name of the executor;
    - `description` is a string. Defines the description of this executor. It will be used in automatic docs UI;
    - `workspace` is a string. Defines the workspace of the executor;
    - `py_modules` is a list of strings. Defines the Python dependencies of the executor;
- `requests` is a map. Defines the mapping from endpoint to class method name;

### Load and Save Executor's YAML config

You can use class method `Executor.load_config` and object method `exec.save_config` to load and save YAML config:

```python
from jina import Executor


class MyExecutor(Executor):

    def __init__(self, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar

    def foo(self, **kwargs):
        pass


y_literal = """
jtype: MyExecutor
with:
  bar: 123
metas:
  name: awesomeness
  description: my first awesome executor
requests:
  /random_work: foo
"""

exec = Executor.load_config(y_literal)
exec.save_config('y.yml')
Executor.load_config('y.yml')
```

### Use Executor out of the Flow

`Executor` object can be used directly just like a regular Python object. For example,

```python
from jina import Executor, requests, DocumentArray, Document


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'


m = MyExec()
da = DocumentArray([Document(text='test')])
m.foo(da)
print(da)
```

```text
DocumentArray has 1 items:
{'id': '20213a02-bdcd-11eb-abf1-1e008a366d48', 'mime_type': 'text/plain', 'text': 'hello world'}
```

This is useful in debugging an Executor.

### Close Executor

You might need to execute some logic when your executor's destructor is called. For example, let's suppose you want to
persist data to the disk (e.g in-memory indexed data, fine-tuned model,...). To do so, you can overwrite the
method `close` and add your logic.

```python
from jina import Executor, requests, Document, DocumentArray


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(doc.text)

    def close(self):
        print("closing...")


with MyExec() as executor:
    executor.foo(DocumentArray([Document(text='hello world')]))
```

```text
hello world
closing...
```