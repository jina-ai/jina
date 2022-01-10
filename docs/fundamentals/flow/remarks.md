# Remarks


## Joining/Reducing

If you have multiple Executors running in parallel and one pod that needs them, merging of the 
resulting Documents is applied automatically if you don't specify `uses` or `uses_before`. You can also customize the 
default reducing logic using a Merger Executor in `uses_before` or `uses`.

Combining `docs` from multiple requests is already done before feeding them to the Executor's
function. Hence, simple joining is just returning this `docs`. However, if you wish to perform more complex logic, you 
can make your endpoints expect a `docs_matrix` object which is a list of DocumentArrays coming from all Executors. You 
can then process them and return the resulting DocumentArray

```python
from jina import Executor, requests, Flow, Document

def print_fn(resp):
    for doc in resp.docs:
        print(doc.text)

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


```

````{tab} Default Reduce
```python
f = Flow().add(uses=A).add(uses=B, needs='gateway').add(needs=['executor0', 'executor1'])

with f:
    f.post(on='/some_endpoint',
           inputs=[Document() for _ in range(3)],
           on_done=print_fn)
```

```text
hello 0
hello 1
hello 2
```
````

````{tab} Simple Custom Reduce
```python
class C(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # 6 docs
        return docs

f = Flow().add(uses=A).add(uses=B, needs='gateway').add(uses=C, needs=['executor0', 'executor1'])

with f:
    f.post(on='/some_endpoint',
           inputs=[Document() for _ in range(3)],
           on_done=print_fn)
```
```text
world 0
world 1
world 2
hello 0
hello 1
hello 2
```
````

````{tab} Custom Reduce with docs_matrix
```python
class C(Executor):

    @requests
    def foo(self, docs_matrix: List[DocumentArray], **kwargs):
        da = DocumentArray()
        for doc1, doc2 in zip(docs_matrix[0], docs_matrix[1]):
            da.append(Document(text=f'{doc1.text}-{doc2.text}'))
        return da

f = Flow().add(uses=A).add(uses=B, needs='gateway').add(uses=C, needs=['executor0', 'executor1'])

with f:
    f.post(on='/some_endpoint',
           inputs=[Document() for _ in range(3)],
           on_done=print_fn)
```
```text
world 0-hello 0
world 1-hello 1
world 2-hello 2
```
````

````{tab} Custom Reduce with modification
You can also modify the Documents while merging:

```python
class C(Executor):

    @requests
    def foo(self, docs, **kwargs):
        # 6 docs
        for d in docs:
            d.text += '!!!'
        return docs

f = Flow().add(uses=A).add(uses=B, needs='gateway').add(uses=C, needs=['executor0', 'executor1'])
with f:
    f.post(on='/some_endpoint',
           inputs=[Document() for _ in range(3)],
           on_done=print_fn)
```
```text
hello 0!!!
hello 1!!!
hello 2!!!
world 0!!!
world 1!!!
world 2!!!
```
````


## multiprocessing Spawn

Few cases require to use `spawn` start method for multiprocessing. 
(e.g.- Cannot re-initialize CUDA in forked subprocess. To use CUDA with multiprocessing, you must use the 'spawn' start method)

- Please set `JINA_MP_START_METHOD=spawn` before starting the Python script to enable this.

    ````{hint}
    There's no need to set this for Windows, as it only supports spawn method for multiprocessing. 
    ````

- Define & start the Flow via an explicit function call inside `if __name__ == '__main__'`. For example

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


- **Avoid un-picklable objects**

    [Here's a list of types that can be pickled in Python](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled). Since `spawn` relies on pickling, we should avoid using code that cannot be pickled.

    ````{hint}
    Here are a few errors which indicates that you are using some code that is not pickable.

    ```bash
    pickle.PicklingError: Can't pickle: it's not the same object
    AssertionError: can only join a started process
    ```

    ````

    Inline functions, such as nested or lambda functions are not picklable. Use `functools.partial` instead.

- **Always provide absolute path**

    While passing filepaths to different jina arguments (e.g.- `uses`, `py_modules`), always pass the absolute path.





## Debugging Executor in a Flow

Standard Python breakpoints will not work inside `Executor` methods when called inside a Flow context manager. Nevertheless, `import epdb; epdb.set_trace()` will work just as a native python breakpoint. Note that you need to `pip install epdb` to have acces to this type of breakpoints.


````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow, Executor, requests
 
class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        a = 25
        import epdb; epdb.set_trace() 
        print(f'\n\na={a}\n\n')
 
def main():
    f = Flow().add(uses=CustomExecutor)
    with f:
        f.post(on='')

if __name__ == '__main__':
    main()

```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow, Executor, requests
 
class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        a = 25
        breakpoint()
        print(f'\n\na={a}\n\n')
 
def main():
    f = Flow().add(uses=CustomExecutor)
    with f:
        f.post(on='')
 
if __name__ == '__main__':
    main()
```
````

