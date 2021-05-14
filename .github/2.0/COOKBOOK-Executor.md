Document, Executor, Flow are three fundamental concepts in Jina.

- [**Document**](COOKBOOK-Document.md) is the basic data type in Jina;
- [**Executor**](COOKBOOK-Executor.md) is how Jina processes Documents;
- **Flow** is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

---

# Temporary Cookbook on `Executor` 2.0 API

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
    - [Multiple binding: `@requests(on=[...])`](#multiple-binding-requestson)
  - [Method Signature](#method-signature)
  - [Method Arguments](#method-arguments)
  - [Method Returns](#method-returns)
  - [YAML Interface](#yaml-interface)
  - [Load and Save Executor's YAML config](#load-and-save-executors-yaml-config)
- [Executor Built-in Features](#executor-built-in-features)
  - [1.x vs 2.0](#1x-vs-20)
  - [Workspace](#workspace)
  - [Metas](#metas)
- [Flow/Client API](#flowclient-api)
  - [`post` method](#post-method)
- [Migration in Practice](#migration-in-practice)
  - [`jina hello fashion`](#jina-hello-fashion)
    - [Encoder](#encoder)
- [Remarks](#remarks)
  - [Joining/Merging](#joiningmerging)

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

`my.yml`:

```yaml
jtype: MyExecutor
with:
  bar: 123
metas:
  name: awesomeness
  description: my first awesome executor
requests:
  /random_work: foo
```

```python
from jina import Executor, Flow, Document


class MyExecutor(Executor):

  def __init__(self, bar: int, **kwargs):
    super().__init__(**kwargs)
    self.bar = bar

  def foo(self, **kwargs):
    print(f'foo says: {self.bar} {self.metas} {kwargs}')


f = Flow().add(uses='my.yml')

with f:
  f.post(on='/random_work', inputs=Document(), on_done=print)
```

## Executor API

- All `executor` come from `Executor` class directly.
- An `executor` class can contain arbitrary number of functions with arbitrary names. It is a bag of functions with
  shared state (via `self`).
- Functions decorated by `@requests` will be invoked according to their `on=` endpoint.

### Inheritance

Every new executor should be inherited directly from `jina.Executor`.

The 1.x inheritance tree is removed,  `Executor` does not have polymorphism anymore.

You can name your executor class freely.

### `__init__` Constructor

If your executor defines `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
in the body, e.g.

```python
from jina import Executor


class MyExecutor(Executor):

  def __init__(self, foo: str, bar: int, **kwargs):
    super().__init__(**kwargs)
    self.bar = bar
    self.foo = foo
```

Here, `kwargs` contains `metas` and `requests` values from YAML config. Note that you can access the value of `metas`
/`requests` in `__init__` body via `self.metas`/`self.requests`, or modifying their values before sending
to `super().__init__()`.

### Method naming

`Executor`'s method can be named freely. Methods are not decorated with `@requests` are irrelevant to Jina.

### `@requests` decorator

`@requests` defines when a function will be invoked. It has a keyword `on=` to define the endpoint.

To call an Executor's function, uses `Flow.post(on=..., ...)`. For example, given

```python
from jina import Executor, Flow, requests


class MyExecutor(Executor):

  @requests(on='/index')
  def foo(self, **kwargs):
    print(kwargs)

  @requests(on='/random_work')
  def bar(self, **kwargs):
    print(kwargs)


f = Flow().add(uses=MyExecutor)

with f:
  pass
```

Then:

- `f.post(on='/index', ...)` will trigger `MyExecutor.foo`;
- `f.post(on='/random_work', ...)` will trigger `MyExecutor.bar`;
- `f.post(on='/blah', ...)` will throw an error, as no function bind with `/blah`;

#### Default binding: `@requests` without `on=`

A class method decorated with plain `@requests` (without `on=`) is the default handler for all endpoints. That means, it
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

#### Multiple binding: `@requests(on=[...])`

To bind a method with multiple endpoints, one can use `@requests(on=['/foo', '/bar'])`. This allows
either `f.post(on='/foo', ...)` or `f.post(on='/bar', ...)` to invoke that function.

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

The arguments order is designed as common-usage-first. Not based on alphabetical order or semantic closeness.

If you don't need some arguments, you can suppress it into `**kwargs`. For example:

```python
@requests
def foo(docs, **kwargs):
  bar(docs)


@requests
def foo(docs, parameters, **kwargs):
  bar(docs)
  bar(parameters)


@requests
def foo(**kwargs):
  bar(kwargs['docs_matrix'])
```

### Method Returns

Method decorated with `@request` can return `Optional[DocumentSet]`. If not `None`, then the current `Request.docs` will
be overridden by the return value.

If return is just a shallow copy of `Request.docs`, then nothing happens.

### YAML Interface

Executor can be load from and stored to a YAML file. The YAML file has the following format:

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
- `metas` is a map. Defines the meta information of that class, comparing to `1.x` it is reduced to the following fields:
  - `name` is a string. Defines the name of the executor;
  - `description` is a string. Defines the description of this executor. It will be used in automatics docs UI;
  - `workspace` is a string. Defines the workspace of the executor
  - `py_modules` is a list of string. Defines the python dependencies of the executor.
- `requests` is a map. Defines the mapping from endpoint to class method name.

### Load and Save Executor's YAML config

You can use class method `Executor.load_config` and object method `exec.save_config` to load & save YAML config as
follows:

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

In 2.0 Executor class has few built-in features than in 1.x. The design principles are (`user` here means "Executor
developer"):

- **Do not surprise user**: keep `Executor` class as Pythonic as possible, it should be as light and less intrusive as a `mixin` class:
  - do not customize the class constructor logic;
  - do not change its builtin interface `__getstate__`, `__setstate__`;
  - do not add new members to the `Executor` object unless we must.
- **Do not overpromise to user**: do not promise features that we can hardly deliver. Trying to control the interface
  while delivering just loosely implemented features is bad for scaling the core framework. For example, `save`, `load`
  , `on_gpu`, etc.

We want to give back the programming freedom to user. If a user is a good Python programmer, he/she should pick
up `Executor` in no time - not spending extra time on learning the implicit boilerplate as in 1.x. Plus,
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
| `metas` config | Moved to `self.metas.xxx`. [Number of fields are greatly reduced](#yaml-interface). |
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

![](workspace-inherit.svg?raw=true)

### Metas

The meta attributes of an `Executor` object are now gathered in `self.metas`, instead of directly posing them to `self`,
e.g. to access `name` use `self.metas.name`.



### `.metas` & `.runtime_args`

An `Executor` object by default contains two attributes `.metas` and `.runtime_args`. They are both in `SimpleNamespace` type and contains some key-value information. However, they are initiated and serve differently.

- **`.metas` are statically initiated.** "Static" means, e.g. from hardcoded value in the code, from a YAML file. Currently, it only supports the following fields: `name`, `description`, `py_modules`, `workspace`.  
- **`.runtime_args` are dynamically assigned during runtime.** Means that you don't know the value before running the `Executor`, e.g. `pea_id`, `replicas`, `replica_id`. 

Note that, YAML API will ignore `.runtime_args` as they are not for statically stored.

---

## Flow/Client API

### `post` method

`post` is the core method. All 1.x methods, e.g. `index`, `search`, `update`, `delete` are just sugary syntax of `post`
by specifying `on='/index'`, `on='/search'`, etc.

```python
def post(
        self,
        on: str,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[dict] = None,
        target_peapod: Optional[str] = None,
        **kwargs,
) -> None:
  """Post a general data request to the Flow.

  :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
  :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
  :param on_done: the function to be called when the :class:`Request` object is resolved.
  :param on_error: the function to be called when the :class:`Request` object is rejected.
  :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
  :param target_peapod: a regex string represent the certain peas/pods request targeted
  :param parameters: the kwargs that will be sent to the executor
  :param kwargs: additional parameters
  :return: None
  """
```

Comparing to 1.x Client/Flow API, the three new arguments are:

- `on`: endpoint, as explained above
- `parameters`: the kwargs that will be sent to the executor, as explained above
- `target_peapod`: a regex string represent the certain peas/pods request targeted

--- 

## Migration in Practice

### `jina hello fashion`

#### Encoder

Left is 1.x, right is 2.0.

![img.png](migration-fashion.png?raw=true)

Line number corresponds to the 1.x code:

- `L5`: change imports to top-level namespace `jina`;
- `L8`: all executors now subclass from `Executor` class;
- `L13-14`: there is no need to inherit from `__init__`, no signature is enforced;
- `L20`: `.touch()` is removed; for this particular encoder as long as the seed is fixed there is no need to store;
- `L22`: adding `@requests` to decorate the core method, changing signature to `docs, **kwargs`;
- `L32`:
  - the content extraction and embedding assignment are now done manually;
  - replacing previous `Blob2PngURI` and `ExcludeQL` driver logic using `Document` built-in methods `convert_blob_to_uri` and `pop`
  - there is nothing to return, as the change is done in-place.

## Remarks

### Joining/Merging

Combining `docs` from multiple requests is already done by the `ZEDRuntime` before feeding to Executor's function.
Hence, simple joining is just returning this `docs`. Complicated joining should be implemented at `Document`
/`DocumentArray`

```python
from jina import Executor, requests, Flow, Document


class C(Executor):

  @requests
  def foo(self, docs, **kwargs):
    # 6 docs
    return docs


class B(Executor):

  @requests
  def foo(self, docs, **kwargs):
    # 3 docs
    for idx, d in enumerate(docs):
      d.text = f'hello {idx}'


class A(Executor):

  @requests
  def A(self, docs, **kwargs):
    # 3 docs
    for idx, d in enumerate(docs):
      d.text = f'world {idx}'


f = Flow().add(uses=A).add(uses=B, needs='gateway').add(uses=C, needs=['pod0', 'pod1'])

with f:
  f.post(on='/some_endpoint',
         inputs=[Document() for _ in range(3)],
         on_done=print)
```

You can also modify the docs while merging, which is not feasible to do in 1.x, e.g.

```python
class C(Executor):

  @requests
  def foo(self, docs, **kwargs):
    # 6 docs
    for d in docs:
      d.text += '!!!'
    return docs
```
