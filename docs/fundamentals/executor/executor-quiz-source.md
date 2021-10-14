# Executor Quiz

### 1. What does an Executor do?

- An Executor is the tool you use to execute your Flow from the CLI: `execute jina_app.py`.
- An Executor performs a single task on a `Document` or `DocumentArray`, like segmenting or encoding it.
- An Executor is a processing pipeline for indexing or querying a dataset.

> [An Executor](https://docs.jina.ai/fundamentals/executor/) represents a processing component in a Jina Flow. It performs a single task on a `Document` or `DocumentArray`.


### 2. Which of the following usages of `requests` are valid?

-   ```python
        @requests(on='/index')
        def foo(self, **kwargs):
            print(f'foo is called: {kwargs}')
    ```

-   ```python
        @requests
        def foo(self, **kwargs):
            print(f'foo is called: {kwargs}')
    ```

-   ```python
        @requests('/index')
        def foo(self, **kwargs):
            print(f'foo is called: {kwargs}')
    ```

> [`@requests`](https://docs.jina.ai/fundamentals/executor/executor-api/#method-decorator) defines when a function will be invoked in the Flow. It has a keyword `on=` to define the endpoint.

### 3. What **should** an Executor method return?

- Nothing.
- It should yield the processed `Document`.
- It should return the processed `DocumentArray`.
- Whatever you like.

> Methods decorated with `@request` can [return `Optional[DocumentArray]`](https://docs.jina.ai/fundamentals/executor/executor-api/#method-returns). The return is optional. **All changes happen in-place**.

### 4. Can you use an Executor outside of a Flow?

- Yes, just like an ordinary Python object
- Yes, but you need to use `jina.executor.load_executor` function
- No

> An `Executor` object can be used directly [just like a regular Python object](https://docs.jina.ai/fundamentals/executor/executor-built-in-features/#use-executor-out-of-flow).

### 5. What formats are supported for creating Executors?

- YAML
- Python
- JSON
- JinaScript

> Besides building an Executor in Python, [an Executor can be loaded from and stored to a YAML file](https://docs.jina.ai/fundamentals/executor/executor-built-in-features/#yaml-interface). JinaScript is not a thing!

### 6. When creating an Executor with multiple Python files, how should it be organized?

- As a zip file
- Directly as a git repo
- As a Python package in a git repo
- Jina doesn't support multi-file Executors

> When you are working with multiple python files, [you should organize them as a Python package](https://docs.jina.ai/fundamentals/executor/repository-structure/) and put them in a special folder inside your repository (as you would normally do with Python packages). 

### 7. What's the recommended way to share Executors with a colleague?

- Send them a link to the repo
- Dockerize your Executor and push directly to Docker Hub
- Push your Executor to Pypi and ask them to install via `pip`
- Push your Executor to Jina Hub

> By using [Jina Hub](https://docs.jina.ai/advanced/hub/) you can pull prebuilt Executors to dramatically reduce the effort and complexity needed in your search system, or push your own custom Executors to share privately or publicly.

### 8. How would you create a new Hub Executor from the CLI?

- `jina hub create <executor_name>`
- `jina hub new`
- `cat executor.py | jina hub`

> Running [`jina hub new`](https://docs.jina.ai/advanced/hub/create-hub-executor/#create-executor) starts a wizard that will ask you some questions to build your Executor.

### 9. How would you use an Executor from Hub directly in your Python code?

-   ```python
    from jina import Flow

    f = Flow().add(uses='jinahub+docker://executor_name')
    ```

-   ```python
    from jina import Flow, Hub

    executor = Hub.pull("executor_name")

    f = Flow().add(uses=executor)
    ```

-   ```python
    from jina import Flow

    f = Flow().add(uses=executor, from="hub")
    ```

> To [use an Executor from Hub](https://docs.jina.ai/advanced/hub/use-hub-executor/) you need to use `.add(uses=jinahub+docker://executor_name)`.

### 10. How would you publish a **private** Executor?

- `jina hub push --private <path_to_executor_folder>`.
- `jina hub private push <path_to_executor_folder>`.
- `jina hub push` then log in to Jina Hub front-end to set it as private.

> When [publishing your Executor](https://docs.jina.ai/advanced/hub/push-executor/#publish-executor) you simply need to use the `--private` argument. Anyone who wants to use that Executor will need to know both the name and a `SECRET` hash.
