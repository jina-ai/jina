Document, Executor, and Flow are the three fundamental concepts in Jina.

- [**Document**](Document.md) is the basic data type in Jina;
- [**Executor**](Executor.md) is how Jina processes Documents;
- [**Flow**](Flow.md) is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

---

# Cookbook on `Executor` 2.0 API

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [Minimum working example](#minimum-working-example)
  - [Pure Python](#pure-python)
  - [With YAML](#with-yaml)
- [Executor API](#executor-api)
  - [Inheritance](#inheritance)
  - [`__init__` Constructor](#__init__-constructor)
  - [Method naming](#method-naming)
  - [`@requests` decorator](#requests-decorator)
    - [Default binding: `@requests` without `on=`](#default-binding-requests-without-on)
    - [Multiple bindings: `@requests(on=[...])`](#multiple-bindings-requestson)
    - [No binding](#no-binding)
  - [Method Signature](#method-signature)
  - [Method Arguments](#method-arguments)
  - [Method Returns](#method-returns)
    - [Example 1: Embed Documents `blob`](#example-1-embed-documents-blob)
    - [Example 2: Add Chunks by Segmenting Document](#example-2-add-chunks-by-segmenting-document)
    - [Example 3: Preserve Document `id` Only](#example-3-preserve-document-id-only)
  - [YAML Interface](#yaml-interface)
  - [Load and Save Executor's YAML config](#load-and-save-executors-yaml-config)
- [Executor Built-in Features](#executor-built-in-features)
  - [1.x vs 2.0](#1x-vs-20)
  - [Workspace](#workspace)
  - [Metas](#metas)
  - [`.metas` & `.runtime_args`](#metas--runtime_args)
- [Migration in Practice](#migration-in-practice)
  - [Encoder in `jina hello fashion`](#encoder-in-jina-hello-fashion)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum working example

### Pure Python

```python
from jina import Executor, Flow, Document, requests


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        print(kwargs)


f = Flow().add(uses=MyExecutor)

with f:
    f.post(on='/random_work', inputs=Document(), on_done=print)
```

### With YAML

`MyExecutor` described as above.

`my.yml`:

```yaml
jtype: MyExecutor
with:
  bar: 123
metas:
  py_modules:
    - foo.py
  name: awesomeness
  description: my first awesome executor
requests:
  /random_work: foo
```

Construct `Executor` from YAML:
```python
from jina import Executor

my_exec = Executor.load_config('my.yml')
```

Flow uses `Executor` from YAML: 
```python
from jina import Flow, Document

f = Flow().add(uses='my.yml')

with f:
    f.post(on='/random_work', inputs=Document(), on_done=print)
```

## Executor API

`Executor` process `DocumentArray` in-place via functions decorated with `@requests`.

- An `Executor` should subclass directly from `jina.Executor` class.
- An `Executor` class is a bag of functions with shared state (via `self`); it can contain an arbitrary number of
  functions with arbitrary names.
- Functions decorated by `@requests` will be invoked according to their `on=` endpoint.

### Inheritance

Every new executor should be inherited directly from `jina.Executor`.

The 1.x inheritance tree is removed. `Executor` no longer has polymorphism.

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

- If the return not `None`, then the current `docs` field in the `Request` will be overridden by the
  returned `DocumentArray`, which will be forwarded to the next Executor in the Flow.
- If the return is just a shallow copy of `Request.docs`, then nothing happens. This is because the changes are already made in-place, there is no point to assign the value.

So do I need a return? No, unless you must create a new `DocumentArray`. Let's see some examples.

#### Example 1: Embed Documents `blob`

In this example, `encode()` uses some neural network to get the embedding for each `Document.blob`, then assign it to `Document.embedding`. The whole procedure is in-place and there is no need to return anything.

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

In this example, each `Document` is segmented by `get_mesh` and the results are added to `.chunks`. After that, `.buffer` and `.uri` are removed from each `Document`. In this case, all changes happen in-place and there is no need to return anything.

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

In this example, a simple indexer stores incoming `docs` in a `DocumentArray`. Then it recreates a new `DocumentArray` by preserving only `id` in the original `docs` and dropping all others, as the developer does not want to carry all rich info over the network. This needs a return. 

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
- `metas` is a map. Defines the meta information of that class. Compared to `1.x` it is reduced to the following fields:
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

## Executor Built-in Features

In Jina 2.0 the Executor class has fewer built-in features compared to 1.x. The design principles are (`user` here
means "Executor developer"):

- **Do not surprise the user**: keep `Executor` class as Pythonic as possible. It should be as light and unintrusive as
  a `mixin` class:
    - do not customize the class constructor logic;
    - do not change its built-in interfaces `__getstate__`, `__setstate__`;
    - do not add new members to the `Executor` object unless needed.
- **Do not overpromise to the user**: do not promise features that we can hardly deliver. Trying to control the
  interface while delivering just loosely-implemented features is bad for scaling the core framework. For
  example, `save`, `load`
  , `on_gpu`, etc.

We want to give programming freedom back to the user. If a user is a good Python programmer, they should pick
up `Executor` in no time - not spend extra time learning the implicit boilerplate as in 1.x. Plus,
subclassing `Executor` should be easy.

### 1.x vs 2.0

- ❌: Completely removed. Users have to implement it on their own.
- ✅: Preserved.

| 1.x | 2.0 |
| --- | --- |
| `.save_config()` | ✅ |
| `.load_config()` | ✅ |
| `.close()` |  ✅ |
| `workspace` interface |  ✅ [Refactored](#workspace). |
| `metas` config | Moved to `self.metas.xxx`. [Number of fields greatly reduced](#yaml-interface). |
| `._drivers` | Refactored and moved to `self.requests.xxx`. |
| `.save()` | ❌ |
| `.load()` | ❌ |
| `.logger`  | ❌ |
| Pickle interface | ❌ |
| init boilerplates (`pre_init`, `post_init`) | ❌ |
| Context manager interface |  ❌ |
| Inline `import` coding style |  ❌ |

![](1.xvs2.0%20BaseExecutor.svg)

### Workspace

Executor's workspace is inherited according to the following rule (`OR` is a python `or`, i.e. first thing first, if NA
then second):

![](../workspace-inherit.svg?raw=true)

### Metas

The meta attributes of an `Executor` object are now gathered in `self.metas`, instead of directly posting them to `self`
, e.g. to access `name` use `self.metas.name`.

### `.metas` & `.runtime_args`

By default, an `Executor` object contains two collections of attributes: `.metas` and `.runtime_args`. They are both
in `SimpleNamespace` type and contain some key-value information. However, they are defined differently and serve
different purposes.

- **`.metas` are statically defined.** "Static" means, e.g. from hard-coded value in the code, from a YAML file.
- **`.runtime_args` are dynamically determined during runtime.** Means that you don't know the value before running
  the `Executor`, e.g. `pea_id`, `replicas`, `replica_id`. Those values are often related to the system/network
  environment around the `Executor`, and less about the `Executor` itself.

In 2.0rc1, the following fields are valid for `metas` and `runtime_args`:

|||
| --- | --- |
| `.metas` (static values from hard-coded values, YAML config) | `name`, `description`, `py_modules`, `workspace` |
| `.runtime_args` (runtime values from its containers, e.g. `Runtime`, `Pea`, `Pod`) | `name`, `description`, `workspace`, `log_config`, `quiet`, `quiet_error`, `identity`, `port_ctrl`, `ctrl_with_ipc`, `timeout_ctrl`, `ssh_server`, `ssh_keyfile`, `ssh_password`, `uses`, `py_modules`, `port_in`, `port_out`, `host_in`, `host_out`, `socket_in`, `socket_out`, `read_only`, `memory_hwm`, `on_error_strategy`, `num_part`, `uses_internal`, `entrypoint`, `docker_kwargs`, `pull_latest`, `volumes`, `host`, `port_expose`, `quiet_remote_logs`, `upload_files`, `workspace_id`, `daemon`, `runtime_backend`, `runtime_cls`, `timeout_ready`, `env`, `expose_public`, `pea_id`, `pea_role`, `noblock_on_start`, `uses_before`, `uses_after`, `parallel`, `replicas`, `polling`, `scheduling`, `pod_role`, `peas_hosts` |

Note that the YAML API will ignore `.runtime_args` during save and load as they are not statically stored.

Also note that for any other parametrization of the Executor, you can still access its constructor arguments (defined in
the class `__init__`) and the request `parameters`.

---

## Migration in Practice

### Encoder in `jina hello fashion`

Left is 1.x, right is 2.0:

![img.png](../migration-fashion.png?raw=true)

Line number corresponds to the 1.x code:

- `L5`: change imports to top-level namespace `jina`;
- `L8`: all executors now subclass from `Executor` class;
- `L13-14`: there is no need to inherit from `__init__`, no signature is enforced;
- `L20`: `.touch()` is removed; for this particular encoder as long as the seed is fixed there is no need to store;
- `L22`: adding `@requests` to decorate the core method, changing signature to `docs, **kwargs`;
- `L32`:
    - content extraction and embedding assignment are now done manually;
    - replacing previous `Blob2PngURI` and `ExcludeQL` driver logic using `Document` built-in
      methods `convert_blob_to_uri` and `pop`
    - there is nothing to return, as the change is done in-place.


### Fastai


```python
import torch
from fastai.vision.models import resnet18

from jina import Executor, requests, DocumentArray, Document

class ResnetImageEncoder(Executor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.model = resnet18()

     @requests
     def encode(self, docs, **kwargs):
         batch = torch.Tensor(docs.get_attributes('blob'))
         batch_embeddings = self.model(batch).detach().numpy()

         for i,doc in enumerate(docs):
             doc.embedding = batch_embeddings[i]

```

