(prefetch)=
# Rate Limit

Requests always reach to the Flow as fast as possible. If a client sends their request faster than the {class}`~jina.Flow` can process them, this can put a high load on the Flow, which may cause out of memory issues. 

At Gateway, you can control the number of in flight requests **per Client** with the `prefetch` argument. Setting `prefetch=2` lets the API accept only 2 requests per client in parallel, hence limiting the load of the Flow. 

By default `prefetch=1000`. To disable it you can set it to 0.

```{code-block} python
---
emphasize-lines: 8, 10
---

def requests_generator():
    while True:
        yield Document(...)

class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        slow_operation()

# Makes sure only 2 requests reach the Executor at a time.
with Flow().config_gateway(prefetch=2).add(uses=MyExecutor) as f:
    f.post(on='/', inputs=requests_generator)
```

```{danger}
When working with very slow executors and a big amount of data, you must set `prefetch` to some small number to prevent out of memory problems. If you are unsure, always set `prefetch=1`.
```


````{tab} Python

```python
from jina import Flow

f = Flow().config_gateway(protocol='http', prefetch=10)
```
````

````{tab} YAML
```yaml
jtype: Flow
with:
  protocol: 'http'
  prefetch: 10
```
````


## Set timeouts

You can set timeouts for sending requests to the {class}`~jina.Executor`s within a {class}`~jina.Flow` by passing the `timeout_send` parameter. The timeout is specified in milliseconds. By default, it is `None` and the timeout is disabled.

If you use timeouts, you may also need to set the {ref}`prefetch <prefetch>` option in the Flow. Otherwise, requests may queue up at an Executor and eventually time out.

```{code-block} python
with Flow().config_gateway(timeout_send=1000) as f:
    f.post(on='/', inputs=[Document()])
```
The example above limits every request to the Executors in the Flow to a timeout of 1 second.
