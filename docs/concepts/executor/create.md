(create-executor)=
# Create

## Introduction

```{tip}
Executors use `docarray.DocumentArray` as their input and output data structure. [Read DocArray's docs](https://docs.docarray.org) to see how it works.
```

An {class}`~jina.Executor` is a self-contained microservice exposed using the gRPC protocol. 
It contains functions (decorated with `@requests`) that process `DocumentArray`s. Executors follow three principles:

1. An Executor should subclass directly from the `jina.Executor` class.
2. An Executor class is a bag of functions with shared state or configuration (via `self`); it can contain an arbitrary number of
functions with arbitrary names.
3. Functions decorated by {class}`~jina.requests` are invoked according to their `on=` endpoint. These functions can be coroutines (`async def`) or regular functions.

## Create an Executor

To create your {class}`~jina.Executor`, run:

```bash
jina hub new
```

<script id="asciicast-T98aWaJLe0r0ul3cXGk7AzqUs" src="https://asciinema.org/a/T98aWaJLe0r0ul3cXGk7AzqUs.js" async></script>

For basic configuration (advanced configuration is optional but rarely necessary), you will be asked for: 

- Your Executor's name
- The path to the folder where it should be saved

After running the command, a project with the following structure will be generated:

```text
MyExecutor/
├── executor.py
├── config.yml
├── README.md
├── requirements.txt
└── Dockerfile
```

- `executor.py` contains your Executor's main logic.
- `config.yml` is the Executor's {ref}`configuration <executor-yaml-spec>` file, where you can define `__init__` arguments using the `with` keyword. You can also define meta annotations relevant to the Executor, for getting better exposure on Executor Hub.
- `requirements.txt` describes the Executor's Python dependencies.
- `README.md` describes how to use your Executor.
- `Dockerfile` is only generated if you choose advanced configuration.

For a more detailed breakdown of the file structure, see `{ref} here <executor-file-structure>`.

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


## Tips

* Use `jina hub new` CLI to create an Executor: To create an Executor, always use this command and follow the instructions. This ensures the correct file 
structure.
* You don't need to manually write a Dockerfile: The build system automatically generates an optimized Dockerfile according to your Executor package.

```{tip}
In the `jina hub new` wizard you can choose from four Dockerfile templates: `cpu`, `tf-gpu`, `torch-gpu`, and `jax-gpu`.
```
