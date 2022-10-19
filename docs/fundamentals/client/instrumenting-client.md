(instrumenting-client)=
# Instrumentation

The {class}`~jina.Client` supports tracing the request which leads to an end-to-end view of a request lifecycle. The **gRPC**, **HTTP** and **WebSocket** protocols are supported.

## Example

````{tab} Implicit, inside a Flow

```{code-block} python
---
emphasize-lines: 6
---
from jina import Flow

f = Flow(
        tracing=True, 
        traces_exporter_host='localhost', 
        traces_exporter_port=4317,
    )

with f:
    f.post('/')
```

````

````{tab} Explicit, outside a Flow

```{code-block} python
---
emphasize-lines: 3,4
---
from jina import Client

# must match the Flow setup
c = Client(
    tracing=True,
    traces_exporter_host='localhost',
    traces_exporter_port=4317,
)
c.post('/')
```

````

Each protocol client creates the first trace id which will be propagated to the `Gateway`. The `Gateway` in turn creates child spans using the available trace id which is further propagated to each Executor request. Using the trace id, all associated span can be collected to build a trace view of the whole request lifecycle.

```{admonition} Using custom/external tracing context
:class: caution
The {class}`~jina.Client` currently doesn't support external tracing context which can potentially be extracted from an upstream request.
```

## See further

- [Tracing in OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/traces/)
- {ref}`Instrumenting a Flow <instrumenting-flow>`
- {ref}`How to deploy and use OpenTelemetry in Jina <opentelemetry>`
