# Troubleshooting on Multiprocessing

When running a Jina Flow locally, you may encounter errors caused by `multiprocessing` package depending on your operating system and Python version. Here are some suggestions:

- Define & start the Flow via an explicit function call inside `if __name__ == '__main__'`, **especially when using `spawn` multiprocessing start method**. For example

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

- Declare Executors on the top-level of the module 

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

- **Always provide absolute path**

    While passing filepaths to different jina arguments (e.g.- `uses`, `py_modules`), always pass the absolute path.



## Using Multiprocessing Spawn

When you encounter this error,

```console
Cannot re-initialize CUDA in forked subprocess. To use CUDA with multiprocessing, you must use the 'spawn' start method
```

- Please set `JINA_MP_START_METHOD=spawn` before starting the Python script to enable this.

    ````{hint}
    There's no need to set this for Windows, as it only supports spawn method for multiprocessing. 
    ````
- **Avoid un-picklable objects**

    [Here's a list of types that can be pickled in Python](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled). Since `spawn` relies on pickling, we should avoid using code that cannot be pickled.

    ````{hint}
    Here are a few errors which indicates that you are using some code that is not pickable.

    ```text
    pickle.PicklingError: Can't pickle: it's not the same object
    AssertionError: can only join a started process
    ```

    ````

    Inline functions, such as nested or lambda functions are not picklable. Use `functools.partial` instead.


## Using Multiprocessing Fork on macOS

Apple has changed the rules for using Objective-C between `fork()` and `exec()` since macOS 10.13.
This may break some codes that use `fork()` in macOS.
For example, the Flow may not be able to start properly with error messages similar to:

```bash
objc[20337]: +[__NSCFConstantString initialize] may have been in progress in another thread when fork() was called.
objc[20337]: +[__NSCFConstantString initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.```
```

You can define the environment variable `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` to get around this issue.
Read [here](http://sealiesoftware.com/blog/archive/2017/6/5/Objective-C_and_fork_in_macOS_1013.html) for more details.
