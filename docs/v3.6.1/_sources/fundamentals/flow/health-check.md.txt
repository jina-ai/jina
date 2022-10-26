# Readiness & health check
Every Jina Flow consists of a {ref}`number of microservices <architecture-overview>`,
each of which have to be healthy before the Flow is ready to receive requests.

Each Flow microservice provides a health check in the form of a [standardized gRPC endpoint](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) that exposes this information to the outside world.
This means that health checks can automatically be performed by Jina itself as well as external tools like Docker Compose, Kubernetes service meshes, or load balancers.

In most cases, it is most useful to check if an entire Flow is ready to accept requests.
To enable this readiness check, the Jina Gateway can aggregate health check information from all services and provides
a readiness check endpoint for the complete Flow.

## Readiness of complete Flow

A lot of times, it is useful to know if a Flow, as a complete set of microservices, is ready to receive requests. This is why the Gateway 
exposes an endpoint for each of the supported protocols to know the health and readiness of the entire Flow. 

Jina `Flow` and `Client` offer a convenient API to query these readiness endpoints. You can call `flow.dry_run()` or `client.dry_run()`, which will return `True` if the Flow is healthy and ready, and `False` otherwise:

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

### Flow status using third-party clients

You can check the status of a Flow using any gRPC/HTTP/Websocket client, not just Jina's Client implementation.

To see how this works, first instantiate the Flow with its corresponding protocol and block it for serving:

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

#### Using gRPC

When using grpc, you can use [grpcurl](https://github.com/fullstorydev/grpcurl) to hit the Gateway's gRPC service that is responsible for reporting the Flow status.

```shell
docker pull fullstorydev/grpcurl:latest
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaGatewayDryRunRPC/dry_run
```
The error-free output below signifies a correctly running Flow:
```text
{
  
}
```

You can simulate an Executor going offline by killing its process.

```shell script
kill -9 $EXECUTOR_PID # in this case we can see in the logs that it is 19059
```

Then by doing the same check, you will see that it returns an error:

```shell
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaGatewayDryRunRPC/dry_run
```

````{dropdown} Error output
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
````


#### Using HTTP or Websocket

When using HTTP or Websocket as the Gateway protocol, you can use curl to target the `/dry_run` endpoint and get the status of the Flow.


```shell
curl http://localhost:12345/dry_run
```
The error-free output below signifies a correctly running Flow:
```text
{"code":0,"description":"","exception":null}%
```

You can simulate an Executor going offline by killing its process.

```shell script
kill -9 $EXECUTOR_PID # in this case we can see in the logs that it is 19059
```

Then by doing the same check, you will see that the call returns an error:

```text
{"code":1,"description":"failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down.","exception":{"name":"InternalNetworkError","args":["failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down."],"stacks":["Traceback (most recent call last):\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 726, in task_wrapper\n    timeout=timeout,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 241, in send_requests\n    await call_result,\n","  File \"/home/joan/.local/lib/python3.7/site-packages/grpc/aio/_call.py\", line 291, in __await__\n    self._cython_call._status)\n","grpc.aio._call.AioRpcError: <AioRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNAVAILABLE\n\tdetails = \"failed to connect to all addresses\"\n\tdebug_error_string = \"{\"created\":\"@1654074272.702044542\",\"description\":\"Failed to pick subchannel\",\"file\":\"src/core/ext/filters/client_channel/client_channel.cc\",\"file_line\":3134,\"referenced_errors\":[{\"created\":\"@1654074272.702043378\",\"description\":\"failed to connect to all addresses\",\"file\":\"src/core/lib/transport/error_utils.cc\",\"file_line\":163,\"grpc_status\":14}]}\"\n>\n","\nDuring handling of the above exception, another exception occurred:\n\n","Traceback (most recent call last):\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/http/app.py\", line 142, in _flow_health\n    data_type=DataInputType.DOCUMENT,\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/http/app.py\", line 399, in _get_singleton_result\n    async for k in streamer.stream(request_iterator=request_iterator):\n","  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 78, in stream\n    async for response in async_iter:\n","  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 154, in _stream_requests\n    response = self._result_handler(future.result())\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/request_handling.py\", line 148, in _process_results_at_end_gateway\n    partial_responses = await asyncio.gather(*tasks)\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 128, in _wait_previous_and_send\n    self._handle_internalnetworkerror(err)\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 70, in _handle_internalnetworkerror\n    raise err\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 125, in _wait_previous_and_send\n    timeout=self._timeout_send,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 734, in task_wrapper\n    num_retries=num_retries,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 697, in _handle_aiorpcerror\n    details=e.details(),\n","jina.excepts.InternalNetworkError: failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down.\n"],"executor":""}}%
```

(health-check-microservices)=
## Health check of individual microservices

In addition to a performing a readiness check for the entire Flow, it is also possible to check every individual microservice in said Flow,
by utilizing a [standardized gRPC health check endpoint](https://github.com/grpc/grpc/blob/master/doc/health-checking.md).
In most cases this is not necessary, since such checks are performed by Jina, a Kubernetes service mesh or a load balancer under the hood.
Nevertheless, it is possible to perform these checks as a user.

When performing these checks, you can expect on of the following `ServingStatus` responses:
- **`UNKNOWN` (0)**: The health of the microservice could not be determined
- **`SERVING` (1)**: The microservice is healthy and ready to receive requests
- **`NOT_SERVING` (2)**: The microservice is *not* healthy and *not* ready to receive requests
- **`SERVICE_UNKNOWN` (3)**: The health of the microservice could not be determined while performing streaming

````{admonition} See Also
:class: seealso

To learn more about these status codes, and how health checks are performed with gRPC, see [here](https://github.com/grpc/grpc/blob/master/doc/health-checking.md).
````

(health-check-executor)=
### Health check of an Executor

Executors run as microservices exposing gRPC endpoints, and they expose one endpoint for a health and readiness check.

To see how to use it, you can start a Flow inside a terminal and block it to accept requests:

```python
from jina import Flow

f = Flow(protocol='grpc', port=12345).add(port=12346)
with f:
    f.block()
```

On another terminal, you can use [grpcurl](https://github.com/fullstorydev/grpcurl) to send RPC requests to your services.

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
### Health check of the Gateway

Just like each individual Executor, the Gateway also acts as a microservice, and as such it exposes a health check endpoint.

In contrast to Executors however, a Gateway can use gRPC, HTTP, or Websocket, and the health check endpoint changes accordingly.


#### Gateway health check with gRPC

When using gRPC as the protocol to communicate with the Gateway, the Gateway uses the exact same mechanism as Executors to expose its health status: It exposes the [ standard gRPC health check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) to the outside world.

With the same Flow as described before, you can use the same way to check the Gateway status:

```bash
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 grpc.health.v1.Health/Check
```

```text
{
  "status": "SERVING"
}
```


#### Gateway health check with HTTP or Websocket

````{admonition} Caution
:class: caution
For Gateways running with HTTP or Websocket, the gRPC health check response codes outlined {ref}`above <health-check-microservices>` do not apply.

Instead, an error free response signifies healthiness.
````

When using HTTP or Websocket as the protocol for the Gateway, it exposes the endpoint `'/'` that one can query to check the status.

First, crate a Flow with HTTP or Websocket protocol:

```python
from jina import Flow

f = Flow(protocol='http', port=12345).add()
with f:
    f.block()
```
Then, you can query the "empty" endpoint:
```bash
curl http://localhost:12345
```

And you will get a valid empty response indicating the Gateway's ability to serve.
```text
{}%
```