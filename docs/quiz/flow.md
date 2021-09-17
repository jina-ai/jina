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

## 6. How do you create a RESTful gateway for a Flow?

```python
flow = Flow()

with f:
  f.protocol = "http"
  f.port_expose = 12345
  f.block()
```

```python
flow = Flow(protocol="http", port_expose=12345)

with f:
  f.block()
```

```python
flow = Flow()

with f:
  f.gateway(protocol="restful", port=12345)
```

> Jina supports gRPC, WebSocket and RESTful gateways. [To enable a Flow to receive from HTTP requests, you can add protocol='http' in the Flow constructor](https://docs.jina.ai/fundamentals/flow/flow-as-a-service/).

### 7. How would you override the `workspace` directory that an Executor uses?

```python
flow = Flow().add(
    uses=MyExecutor,
    uses_metas={'workspace': 'different_workspace'},
)
```

```python
flow = Flow().add(
    uses=MyExecutor,
    uses_with={'workspace': 'different_workspace'},
)
```

```python
flow = Flow().add(
    uses=MyExecutor(workspace='different_workspace')
)
```

> `workspace` is a meta setting, meaning it applies to *all* Executors in the Flow. [As well as meta-configuration, both request-level and Executor-level parameters can be overridden](https://docs.jina.ai/fundamentals/flow/add-exec-to-flow/#override-executor-config).

## 8. What kind of input does an `AsyncFlow` accept?

- Exactly the same as a standard Flow
- Async generators
- `AsyncDocumentArray`s

> AsyncFlow is an “async version” of the Flow class. Unlike Flow, [AsyncFlow accepts input and output functions as async generators](https://docs.jina.ai/fundamentals/flow/async-flow/#create-asyncflow). This is useful when your data sources involve other asynchronous libraries (e.g. motor for MongoDB):

## 9. What communication protocols does a Flow support?

- SOAP
- gRPC
- WebSocket
- REST
- GraphQL

> Jina supports [HTTP (RESTful), gRPC, and WebSocket protocols](https://docs.jina.ai/fundamentals/flow/flow-as-a-service/#supported-communication-protocols).

## 10. Can you access a Flow service from a web page with a different domain?

- No. Jina only supports access from a web page running on the same machine.
- Yes, out of the box
- Yes, but you have to enable CORS

> CORS (cross-origin-resources-sharing) is [by default disabled for security](https://docs.jina.ai/fundamentals/flow/flow-as-a-service/#enable-cross-origin-resources-sharing-cors). That means you can not access the service from a webpage with different domain until you enable it.

