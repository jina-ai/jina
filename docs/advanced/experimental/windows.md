(jina-on-windows)=
# Jina on Windows

You can install and use Jina on Windows.

However, as Jina is built keeping *nix-based platforms in mind, and the upstream libraries that Jina depends on also follow the similar ideology. Hence, there are some caveats when running Jina on Windows. [If you face additional issues, please let us know.](https://github.com/jina-ai/jina/issues/)

```{caution}
There can be a significant performance impact while running Jina on Windows. You may not want to use it in production.
```

## Known issues

### `multiprocessing` spawn

Jina relies heavily on `multiprocessing` to enable scaling & distribution. Windows only supports [spawn start method for multiprocessing](https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods), which has a few caveats. 

### Compatability of Executors in the Hub

We've added preliminary support to using Executors listed in the Hub portal. Note that, these Executors are based on *nix OS and might not be compatible to run natively on Windows. Containers that are built on Windows OS are not supported yet. 


```{seealso}
[Install Docker Desktop on Windows](https://docs.docker.com/desktop/windows/install/)
```

### JinaD is not supported

We haven't added suppoort to JinaD on Windows. If you can make it work, feel free to create a PR.

### Limited support for `DocumentArrayMemmap`

Even though support for [DocumentArrayMemmap](../../fundamentals/document/documentarraymemmap-api) is added, it is error prone. Please proceed with caution.

### Memory watermark is unavailable 

Since Windows doesn't support `resource` module, memory watermark checks are disabled by default.


## Best practices


### `UnicodeEncodeError` on Jina CLI

```bash
UnicodeEncodeError: 'charmap' codec can't encode character '\u25ae' in position : character maps to <undefined>
```
Set environment variable `PYTHONIOENCODING='utf-8'` before starting your python script.


### Explicit entrypoint

On Windows, the entrypoint of a Jina Flow should always be explicit via `if __name__ == '__main__'`.

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


### Declare Executors on the top-level of the module

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

### Avoid un-picklable objects

[Here's a list of types that can be pickled in Python](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled). Since `spawn` relies on pickling, we should avoid using code that cannot be pickled.

````{hint}
Here are a few errors which indicates that you are using some code that is not pickable.

```bash
pickle.PicklingError: Can't pickle: it's not the same object
AssertionError: can only join a started process
```

````

Inline functions, such as nested or lambda functions are not picklable. Use `functools.partial` instead.

### Always provide absolute path 

While passing filepaths to different jina arguments (e.g.- `uses`, `py_modules`), always pass the absolute path.

