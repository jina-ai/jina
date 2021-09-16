# Flow Quiz

## 1. What does a Flow do?

- The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a dataset.
- The `Flow` is a graphical interface that lets users see how their `Documents` are flowing into the processing pipeline.
- The `Flow` is short for "fast, low-resource" and is a special kind of Executor for low-powered machines.

> [The `Flow` ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a dataset](https://docs.jina.ai/fundamentals/flow/). Documents "flow" through the created pipeline and are processed by Executors.

## 2. What languages can you use to create a Flow?

- Python directly
- YAML
- JSON
- From the command line with `jina flow new`

> Jina supports [creating Flows in both YAML and directly in Python](https://docs.jina.ai/fundamentals/flow/#minimum-working-example)

## 3. How would you create and run a Flow?

```python
from jina import Flow

flow = Flow()

with flow:
   flow.index()
```

```python
from jina import Flow

flow = Flow()
flow.index()
```

```python
from jina import Flow

Flow.index()
```

> To use `flow`, [always open it as a context manager, just like you open a file](https://docs.jina.ai/fundamentals/flow/flow-api/#use-a-flow). This is considered the best practice in Jina.

## 4. What are some valid ways to index a dataset?

```python
with flow:
  flow.index()
```

```python
with flow:
  flow.post('/index')
```

```
with flow:
  flow.post(task='index')
```

> `.post()` is the core method for [sending data to a `Flow` object](https://docs.jina.ai/fundamentals/flow/send-recv/), it provides multiple callbacks for fetching results from the Flow. You can also use CRUD methods (`index`, `search`, `update`, `delete`) which are just sugary syntax of `post`
with `on='/index'` , `on='/search'`, etc.

## 5. How do you add an Executor to a Flow?

```python
from jina import Flow, Executor

class MyExecutor(Executor):
    ...


f = Flow().add(uses=MyExecutor)
```

```python
from jina import Flow, Executor

class MyExecutor(Executor):
    ...


f = Flow().append(MyExecutor)
```

```python
from jina import Flow, Executor

class MyExecutor(Executor):
    ...


f = Flow(executors=[MyExecutor])
```

> The [`uses` parameter](https://docs.jina.ai/fundamentals/flow/add-exec-to-flow/) specifies the Executor. `uses` accepts multiple value types including class name, Docker image, (inline) YAML.
