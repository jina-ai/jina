(executor)=

# Basics

```{tip}
Executors use `docarray.DocumentArray` as their input and output data structure. [Read DocArray's docs](https://docarray.jina.ai) to see how it works.
```

An {class}`~jina.Executor` is a self-contained microservice exposed using the gRPC protocol. 
It contains functions (decorated with `@requests`) that process `DocumentArray`s. To create an Executor, you need to follow three principles:

1. An Executor should subclass directly from the `jina.Executor` class.
2. An Executor class is a bag of functions with shared state or configuration (via `self`); it can contain an arbitrary number of
functions with arbitrary names.
3. Functions decorated by {class}`~jina.requests` are invoked according to their `on=` endpoint. These functions can be coroutines (`async def`) or regular functions.

## Constructor

### Subclass

Every new Executor should be a subclass of {class}`~jina.Executor`. You can name your Executor class freely.

### `__init__`

You only need to implement `__init__` if your Executor contains initial state.

If your Executor has `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)` 
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
:class: hint
Here, `kwargs` are reserved for Jina to inject `metas` and `requests` (representing the request-to-function mapping) values when the Executor is used inside a {ref}`Flow <flow-cookbook>`.

You can access the values of these arguments in the `__init__` body via `self.metas`/`self.requests`/`self.runtime_args`, or modify their values before passing them to `super().__init__()`.
````

## Destructor

You might need to execute some logic when your Executor's destructor is called.

For example, if you want to persist data to disk (e.g. in-memory indexed data, fine-tuned model,...) you can overwrite the {meth}`~jina.serve.executors.BaseExecutor.close` method and add your logic.

Jina ensures the {meth}`~jina.serve.executors.BaseExecutor.close` method is executed when the Executor is terminated inside a {class}`~jina.Deployment` or {class}`~jina.Flow`, or when deployed in any cloud-native environment.

You can think of this as Jina using the Executor as a context manager, making sure that the {meth}`~jina.serve.executors.BaseExecutor.close` method is always executed.

```python
from jina import Executor


class MyExec(Executor):
    def close(self):
        print('closing...')
```

## Attributes

When implementing an Executor, if your Executor overrides `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)`
                                 
```python
from jina import Executor


class MyExecutor(Executor):
    def __init__(self, foo: str, bar: int, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.foo = foo
```

This is important because when an Executor is instantiated in the context of a Flow, Jina adds {ref}`extra arguments <flow-specific-arguments>`.

## See also

- {ref}`Debugging an Executor <debug-executor>`
- {ref}`Using an Executor on a GPU <gpu-executor>`
- {ref}`How to use external Executors <external-executors>`
- {ref}`Custom logging configuration <logging-configuration>`
