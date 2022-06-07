# Health and readiness check of Jina Services

(health-check-executor)=
## Health check of an Executor

Executors run as microservices exposing `grpc` endpoints. To give information to the outside world about their health and their readiness to receive requests,
Executors expose a [grpc health check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) service which can be used by different orchestrators like docker-compose, 
or by other services like load-balancers. Jina itself when run locally uses this service to make sure that each Executor is ready to receive traffic.

To see how to use it, let's start a Flow inside a Terminal and let it blocked to serve requests:

```python
from jina import Flow

f = Flow(protocol='grpc', port=12345).add(port=12346)
with f:
    f.block()
```

On another terminal, we can install or download [grpcurl](https://github.com/fullstorydev/grpcurl) image to be able to send `rpc` requests to our services.

```bash
docker pull fullstorydev/grpcurl:latest
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12346 grpc.health.v1.Health/Check
```

```text
{
  "status": "SERVING"
}
```

(health-check-gateway)=
## Health check of the Gateway

The same way individual Executors expose endpoints for orchestrators, clients or other services to check their availability, Gateway, as a microservice, also exposes this in different ways depending on the protocol used.


### Gateway health check with grpc

When using grpc as the protocol to communicate with the Gateway, then Gateway uses the exact same mechanism as Executors to expose their individual health status. It exposes [grpc health check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) to the outside world.

With the same Flow described before we can use the same way to check the gateway status:

```bash
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 grpc.health.v1.Health/Check
```

```text
{
  "status": "SERVING"
}
```


### Gateway health check with http or websocket

When using grpc or http as a procotol for the Gateway, then it exposes and endpoint '/' that one can query to check the status.

By having a Flow with http or websocket as protocol:

```python
from jina import Flow

f = Flow(protocol='http', port=12345).add()
with f:
    f.block()
```

```bash
curl http://localhost:12345
```

Then you will get a valid empty response indicating its ability to serve.
```text
{}%
```

## Readiness of a Flow exposed to the client

A lot of times, from the client perspective, it is useful to know if a Flow, as a complete set of microservices, is ready to receive requests. This is why the gateway 
exposes an endpoint for each of the supported protocols to know the health and readiness of a Flow. 

Also Jina Flow and Client contains a convenient API to query these endpoints. You can call `flow.dry_run()` and `client.dry_run()`

````{tab} via Flow
```python
from jina import Flow

with Flow().add() as f:
    print(f.dry_run())

print(f.dry_run())
```
```text
True
False
```
````
````{tab} via Client
```python
from jina import Flow

with Flow(port=12345).add() as f:
    f.block()
```
```python
from jina import Client

client = Client(port=12345)
print(client.dry_run())
```
```text
True
```
````

### Check status from outside

To understand better what is going on under the hood, we can check how to target the endpoint from outside Jina or the client.

Let's first instantiate the Flow with its corresponding protocol and block it for serving.

```python
from jina import Flow
import os

PROTOCOL = 'grpc'  # it could also be http or websocket

os.setenv[
    'JINA_LOG_LEVEL'
] = 'DEBUG'  # this way we can check what is the PID of the Executor

with Flow(protocol=PROTOCOL, port=12345).add() as f:
    f.block()
```

```text
⠋  Waiting ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0/0 -:--:--DEBUG  gateway/rep-0@19075 adding connection for deployment executor0/heads/0 to grpc://0.0.0.0:12346                                                                                           [05/31/22 18:10:16]
DEBUG  executor0/rep-0@19074 start listening on 0.0.0.0:12346                                                                                                                                   [05/31/22 18:10:16]
DEBUG  gateway/rep-0@19075 start server bound to 0.0.0.0:12345                                                                                                                                  [05/31/22 18:10:17]
DEBUG  executor0/rep-0@19059 ready and listening                                                                                                                                                [05/31/22 18:10:17]
DEBUG  gateway/rep-0@19059 ready and listening                                                                                                                                                  [05/31/22 18:10:17]
╭────── 🎉 Flow is ready to serve! ──────╮
│  🔗  Protocol                  GRPC    │
│  🏠     Local         0.0.0.0:12345    │
│  🔒   Private    192.168.1.13:12345    │
╰────────────────────────────────────────╯
DEBUG  Flow@19059 2 Deployments (i.e. 2 Pods) are running in this Flow 
```

#### with grpc

When using grpc, we can again use grpcurl to hit the proper grpc service, we will see that the Status is positive.

```shell
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaGatewayDryRunRPC/dry_run
```
```text
{
  
}
```

Let's simulate an Executor going offline by killing its process.

```shell script
kill -9 $EXECUTOR_PID # in this case we can see in the logs that it is 19059
```

Then by doing the same check, we will see that it returns an error.

```shell
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaGatewayDryRunRPC/dry_run
```

```text
{
  "code": "ERROR",
  "description": "failed to connect to all addresses |Gateway: Communication error with deployment at address(es) 0.0.0.0:12346. Head or worker(s) may be down.",
  "exception": {
    "name": "InternalNetworkError",
    "args": [
      "failed to connect to all addresses |Gateway: Communication error with deployment at address(es) 0.0.0.0:12346. Head or worker(s) may be down."
    ],
    "stacks": [
      "Traceback (most recent call last):\n",
      "  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 750, in task_wrapper\n    timeout=timeout,\n",
      "  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 197, in send_discover_endpoint\n    await self._init_stubs()\n",
      "  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 174, in _init_stubs\n    self.channel\n",
      "  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 1001, in get_available_services\n    async for res in response:\n",
      "  File \"/home/joan/.local/lib/python3.7/site-packages/grpc/aio/_call.py\", line 326, in _fetch_stream_responses\n    await self._raise_for_status()\n",
      "  File \"/home/joan/.local/lib/python3.7/site-packages/grpc/aio/_call.py\", line 237, in _raise_for_status\n    self._cython_call.status())\n",
      "grpc.aio._call.AioRpcError: \u003cAioRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNAVAILABLE\n\tdetails = \"failed to connect to all addresses\"\n\tdebug_error_string = \"{\"created\":\"@1654012804.794351252\",\"description\":\"Failed to pick subchannel\",\"file\":\"src/core/ext/filters/client_channel/client_channel.cc\",\"file_line\":3134,\"referenced_errors\":[{\"created\":\"@1654012804.794350006\",\"description\":\"failed to connect to all addresses\",\"file\":\"src/core/lib/transport/error_utils.cc\",\"file_line\":163,\"grpc_status\":14}]}\"\n\u003e\n",
      "\nDuring handling of the above exception, another exception occurred:\n\n",
      "Traceback (most recent call last):\n",
      "  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/grpc/__init__.py\", line 155, in dry_run\n    async for _ in self.streamer.stream(request_iterator=req_iterator):\n",
      "  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 78, in stream\n    async for response in async_iter:\n",
      "  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 154, in _stream_requests\n    response = self._result_handler(future.result())\n",
      "  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/request_handling.py\", line 146, in _process_results_at_end_gateway\n    await asyncio.gather(gather_endpoints(request_graph))\n",
      "  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/request_handling.py\", line 88, in gather_endpoints\n    raise err\n",
      "  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/request_handling.py\", line 80, in gather_endpoints\n    endpoints = await asyncio.gather(*tasks_to_get_endpoints)\n",
      "  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 754, in task_wrapper\n    e=e, retry_i=i, dest_addr=connection.address\n",
      "  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 697, in _handle_aiorpcerror\n    details=e.details(),\n",
      "jina.excepts.InternalNetworkError: failed to connect to all addresses |Gateway: Communication error with deployment at address(es) 0.0.0.0:12346. Head or worker(s) may be down.\n"
    ]
  }
}
```


#### With http or websocket

To understand better what is going on under the hood, we can check how to target the endpoint from outside Jina or the client.

Let's first instantiate the Flow and block it for serving.

Then we can use curl to target the `/dry_run` endpoint.


```shell
curl http://localhost:12345/dry_run
```
```text
{"code":0,"description":"","exception":null}%
```

Let's simulate an Executor going offline by killing its process.

```shell script
kill -9 $EXECUTOR_PID # in this case we can see in the logs that it is 19059
```

Then by doing the same check, we will see that it returns an error.

```text
{"code":1,"description":"failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down.","exception":{"name":"InternalNetworkError","args":["failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down."],"stacks":["Traceback (most recent call last):\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 726, in task_wrapper\n    timeout=timeout,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 241, in send_requests\n    await call_result,\n","  File \"/home/joan/.local/lib/python3.7/site-packages/grpc/aio/_call.py\", line 291, in __await__\n    self._cython_call._status)\n","grpc.aio._call.AioRpcError: <AioRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNAVAILABLE\n\tdetails = \"failed to connect to all addresses\"\n\tdebug_error_string = \"{\"created\":\"@1654074272.702044542\",\"description\":\"Failed to pick subchannel\",\"file\":\"src/core/ext/filters/client_channel/client_channel.cc\",\"file_line\":3134,\"referenced_errors\":[{\"created\":\"@1654074272.702043378\",\"description\":\"failed to connect to all addresses\",\"file\":\"src/core/lib/transport/error_utils.cc\",\"file_line\":163,\"grpc_status\":14}]}\"\n>\n","\nDuring handling of the above exception, another exception occurred:\n\n","Traceback (most recent call last):\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/http/app.py\", line 142, in _flow_health\n    data_type=DataInputType.DOCUMENT,\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/http/app.py\", line 399, in _get_singleton_result\n    async for k in streamer.stream(request_iterator=request_iterator):\n","  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 78, in stream\n    async for response in async_iter:\n","  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 154, in _stream_requests\n    response = self._result_handler(future.result())\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/request_handling.py\", line 148, in _process_results_at_end_gateway\n    partial_responses = await asyncio.gather(*tasks)\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 128, in _wait_previous_and_send\n    self._handle_internalnetworkerror(err)\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 70, in _handle_internalnetworkerror\n    raise err\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 125, in _wait_previous_and_send\n    timeout=self._timeout_send,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 734, in task_wrapper\n    num_retries=num_retries,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 697, in _handle_aiorpcerror\n    details=e.details(),\n","jina.excepts.InternalNetworkError: failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down.\n"],"executor":""}}%
```
