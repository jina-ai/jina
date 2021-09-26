# Jina on Windows

Jina is built keeping *nix based platforms in mind. Few of the upstream libraries that jina relies on also follow a similar ideology. Having said that, we made a few changes to add basic support on Windows. 

```{caution}
There can be a significant performance impact while running Jina on Windows. Use with caution!
```

This document tries to summarize caveats to make Jina function smoothly on Windows. [If you face additional issues, please let us know.](https://github.com/jina-ai/jina/issues/new/choose)


```{note}
Jina relies heavily on `multiprocessing` to enable scaling & distribution. Windows only supports [spawn start method for multiprocessing](https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods), which has a few caveats. 
```

## 💡 Tips

### Entrypoint

The entrypoint for Flow invocation should always be via `if __name__ == '__main__'`.

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 13, 14
---

from jina import Flow, Executor, requests

class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        ...

def main():
    f = Flow().add(uses=CustomExecutor)
    with f:
        ...

if __name__ == '__main__':
    main()
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 2
---

from jina import Flow, Executor, requests

class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        ...

f = Flow().add(uses=CustomExecutor)
with f:
    ...

"""
# error
This probably means that you are not using fork to start your
child processes and you have forgotten to use the proper idiom
in the main module:

    if _name_ == '_main_':
        freeze_support()
        ...

The "freeze_support()" line can be omitted if the program
is not going to be frozen to produce an executable.

"""
```

````

### Avoid using code that is not picklable

[Here's a list of types that can be pickled in Python](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled). Since `spawn` relies on pickling, we should avoid using code that cannot be pickled.

``` {hint}
Here are a few errors which indicates that you are using some code that is not pickable.

`pickle.PicklingError: Can't pickle: it's not the same object`

`AssertionError: can only join a started process`

```

#### Declare Executors on the top-level of the module

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 1
---

class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        ...

def main():
    f = Flow().add(uses=Executor)
    with f:
        ...

```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 2
---

def main():
    class CustomExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            ...

    f = Flow().add(uses=Executor)
    with f:
        ...
```
````

#### Avoid using `lambda` functions

Nested functions & Lambda functions are not picklable. Use `functools.partial` instead.

### Using Executors from Hub

We've added preliminary support to using Executors listed in the Hub portal. Note that, these Executors are based on *nix OS and might not be compatible to run natively on Windows. Containers that are built on Windows OS are not supported yet. 


```{seealso}
[Install Docker Desktop on Windows](https://docs.docker.com/desktop/windows/install/)
```

### Always provide absolute path 

While passing filepaths to different jina arguments (e.g.- `uses`, `py_modules`), always pass the absolute path.

### JinaD is not supported

We haven't added suppoort to JinaD on Windows. If you can make it work, feel free to create a PR.

### Memory watermark disabled

Since Windows doesn't support `resource` module, memory watermark checks are disabled by default.

### Limited support for `DocumentArrayMemmap`

Even though support for [DocumentArrayMemmap](../../fundamentals/document/documentarraymemmap-api) is added, it is error prone. Please proceed with caution.

### UnicodeEncodeError while using jina cli

```python
UnicodeEncodeError: 'charmap' codec can't encode character '\u25ae' in position : character maps to <undefined>
```
Set environment variable `PYTHONIOENCODING='utf-8'` before starting your python script.
