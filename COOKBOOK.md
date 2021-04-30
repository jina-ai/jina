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
| `parameters`  | `Dict`  | `Request.parameters` |
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



