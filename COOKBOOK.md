# Temporary Cookbook on Jina 2.0

## Minimum working example

```python
from jina import Executor, Flow, Document, requests


class MyExecutor(Executor):

  @requests
  def foo(self, **kwargs):
    print(kwargs)


f = Flow().add(uses=MyExecutor)

with f:
  f.post(Document(),
         on='/random_work',
         on_done=print)
```

## Executor API

### Inheritance

Every new executor should be inherited directly from `jina.Executor`.

The 1.x inheritance tree is removed,  `Executor` does not have polymorphism anymore.

You can name your executor class freely.

### Method naming

`Executor`'s method can be named freely. Methods are not decorated with `@requests` are irrelevant to Jina.

### `@requests` decorator

`@requests` defines when a function will be invoked. It has a keyword `on=` to define the endpoint.

To call an Executor's function, uses `Flow.post(..., on=)`. For example, given

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
# ...
```

Then:

- `f.post(..., on='/index')` will trigger `MyExecutor.foo`;
- `f.post(..., on='/random_work')` will trigger `MyExecutor.bar`;
- `f.post(..., on='/blah')` will throw an error, as no function bind with `/blah`;

### `@requests` decorator without `on=`

A class method decorated with `@requests` is the default handler for all endpoints. That means, it is the fallback
handler for endpoints that are not found. `f.post(..., on='/blah')` will call `MyExecutor.foo`

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

### Method Arguments

The Executor's method receive the following arguments in order:

| Name | Type | Description  | 
| --- | --- | --- |
| `docs`   | `Optional[DocumentSet]`  | `Request.docs`. When multiple requests are available, it is a concatenation of all `Request.docs` as one `DocumentSet`. When `DocumentSet` has zero element, then it is `None`.  |
| `groundtruths`   | `Optional[DocumentSet]`  | `Request.groundtruths`. When `DocumentSet` has zero element, then it is `None`.  |
| `parameters`  | `Dict`  | `Request.parameters`, given by `Flow.post(..., parameters=)` |
| `docs_matrix`  | `List[DocumentSet]`  | When multiple requests are available, it is a list of all `Request.docs`. On single request, it is `None` |
| `groundtruths_matrix`  | `List[DocumentSet]`  | Same behavior as `docs_matrix` but on `Request.groundtruths` |

Note, executor's methods not decorated with `@request` do not enjoy these arguments.

If you don't need some arguments, you can suppress it into `**kwargs`. For example:

```python
@request
def foo(docs, **kwargs):
  bar(docs)


@request
def foo(docs, groundtruths, **kwargs):
  bar(docs)
  bar(groundtruths)


@request
def foo(**kwargs):
  bar(kwargs['docs_matrix'])
```

### Summary

- All `executor` come from `Executor` class directly.
- An `executor` class can contain arbitrary number of functions with arbitrary names. It is a bag of functions with
  shared state (via `self`).
- Functions decorated by `@requests` will be invoked according to their `on=` endpoint.

## Flow/Client API

### `post` method

`post` is the core method. All 1.x methods, e.g. `index`, `search`, `update`, `delete` are just sugary syntax of `post`
by specifing `on='\index'`, `on='\search'`, etc.

```python
def post(
        self,
        inputs: InputType,
        on: str,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[dict] = None,
        target_peapod: Optional[str] = None,
        **kwargs,
) -> None:
  """Post a general data request to the Flow.

  :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
  :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
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


