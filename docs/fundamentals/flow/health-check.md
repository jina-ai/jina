# Readiness & health check
A Jina {class}`~jina.Flow` consists of {ref}`a Gateway and Executors<architecture-overview>`,
all of which have to be healthy before the Flow is ready to receive requests.

A Flow is marked as "ready", when all its Executors and its Gateway are fully loaded and ready.

Each Executor provides a health check in the form of a [standardized gRPC endpoint](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) that exposes this information to the outside world.
This means health checks can be automatically performed by Jina itself, as well as external tools like Docker Compose, Kubernetes service meshes, or load balancers.


## Flow Readiness

In most cases, it is useful to check if an entire Flow is ready to accept requests.
To enable this readiness check, the Jina Gateway can aggregate health check information from all services and provides
a readiness check endpoint for the complete Flow.


<!-- start flow-ready -->

{class}`~jina.Client` offers an API to query these readiness endpoints. You can call {meth}`~jina.clients.mixin.HealthCheckMixin.is_flow_ready` or {meth}`~jina.Flow.is_flow_ready`. It returns `True` if the Flow is ready, and `False` if it is not.

````{tab} via Flow
```python
from jina import Flow

with Flow().add() as f:
    print(f.is_flow_ready())

print(f.is_flow_ready())
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
print(client.is_flow_ready())
```
```text
True
```
````

`````{tab} via CLI
```python
from jina import Flow

with Flow(port=12345).add() as f:
    f.block()
```
```bash
jina ping flow grpc://localhost:12345
```

````{tab} Success
```text
INFO   JINA@92877 ping grpc://localhost:12345 at 0 round...                                                                                              [09/08/22 12:58:13]
INFO   JINA@92877 ping grpc://localhost:12345 at 0 round takes 0 seconds (0.04s)
INFO   JINA@92877 ping grpc://localhost:12345 at 1 round...                                                                                              [09/08/22 12:58:14]
INFO   JINA@92877 ping grpc://localhost:12345 at 1 round takes 0 seconds (0.01s)
INFO   JINA@92877 ping grpc://localhost:12345 at 2 round...                                                                                              [09/08/22 12:58:15]
INFO   JINA@92877 ping grpc://localhost:12345 at 2 round takes 0 seconds (0.01s)
INFO   JINA@92877 avg. latency: 24 ms                                                                                                                    [09/08/22 12:58:16]
```
````

````{tab} Failure
```text
INFO   JINA@92986 ping grpc://localhost:12345 at 0 round...                                                                                              [09/08/22 12:59:00]
ERROR  GRPCClient@92986 Error while getting response from grpc server <AioRpcError of RPC that terminated with:                                          [09/08/22 12:59:00]
               status = StatusCode.UNAVAILABLE
               details = "failed to connect to all addresses; last error: UNKNOWN: Failed to connect to remote host: Connection refused"
               debug_error_string = "UNKNOWN:Failed to pick subchannel {created_time:"2022-09-08T12:59:00.518707+02:00", children:[UNKNOWN:failed to
       connect to all addresses; last error: UNKNOWN: Failed to connect to remote host: Connection refused {grpc_status:14,
       created_time:"2022-09-08T12:59:00.518706+02:00"}]}"
       >
WARNI… JINA@92986 not responding, retry (1/3) in 1s
INFO   JINA@92986 ping grpc://localhost:12345 at 0 round takes 0 seconds (0.01s)
INFO   JINA@92986 ping grpc://localhost:12345 at 1 round...                                                                                              [09/08/22 12:59:01]
ERROR  GRPCClient@92986 Error while getting response from grpc server <AioRpcError of RPC that terminated with:                                          [09/08/22 12:59:01]
               status = StatusCode.UNAVAILABLE
               details = "failed to connect to all addresses; last error: UNKNOWN: Failed to connect to remote host: Connection refused"
               debug_error_string = "UNKNOWN:Failed to pick subchannel {created_time:"2022-09-08T12:59:01.537293+02:00", children:[UNKNOWN:failed to
       connect to all addresses; last error: UNKNOWN: Failed to connect to remote host: Connection refused {grpc_status:14,
       created_time:"2022-09-08T12:59:01.537291+02:00"}]}"
       >
WARNI… JINA@92986 not responding, retry (2/3) in 1s
INFO   JINA@92986 ping grpc://localhost:12345 at 1 round takes 0 seconds (0.01s)
INFO   JINA@92986 ping grpc://localhost:12345 at 2 round...                                                                                              [09/08/22 12:59:02]
ERROR  GRPCClient@92986 Error while getting response from grpc server <AioRpcError of RPC that terminated with:                                          [09/08/22 12:59:02]
               status = StatusCode.UNAVAILABLE
               details = "failed to connect to all addresses; last error: UNKNOWN: Failed to connect to remote host: Connection refused"
               debug_error_string = "UNKNOWN:Failed to pick subchannel {created_time:"2022-09-08T12:59:02.557195+02:00", children:[UNKNOWN:failed to
       connect to all addresses; last error: UNKNOWN: Failed to connect to remote host: Connection refused {grpc_status:14,
       created_time:"2022-09-08T12:59:02.557193+02:00"}]}"
       >
WARNI… JINA@92986 not responding, retry (3/3) in 1s
INFO   JINA@92986 ping grpc://localhost:12345 at 2 round takes 0 seconds (0.02s)
WARNI… JINA@92986 message lost 100% (3/3)
```
````
`````

<!-- end flow-ready -->

### Flow status using third-party clients

You can check the status of a Flow using any gRPC/HTTP/WebSockets client, not just Jina's Client implementation.

To see how this works, first instantiate the Flow with its corresponding protocol and block it for serving:

```python
from jina import Flow
import os

PROTOCOL = 'grpc'  # it could also be http or websocket

os.environ[
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

When using grpc, use [grpcurl](https://github.com/fullstorydev/grpcurl) to access the Gateway's gRPC service that is responsible for reporting the Flow status.

```shell
docker pull fullstorydev/grpcurl:latest
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaGatewayDryRunRPC/dry_run
```
The error-free output below signifies a correctly running Flow:
```json
{}
```

You can simulate an Executor going offline by killing its process.

```shell script
kill -9 $EXECUTOR_PID # in this case we can see in the logs that it is 19059
```

Then by doing the same check, you can see that it returns an error:

```shell
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaGatewayDryRunRPC/dry_run
```

````{dropdown} Error output
```json
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


#### Using HTTP or WebSockets

When using HTTP or WebSockets as the Gateway protocol, use curl to target the `/dry_run` endpoint and get the status of the Flow.


```shell
curl http://localhost:12345/dry_run
```
Error-free output signifies a correctly running Flow:
```json
{"code":0,"description":"","exception":null}
```

You can simulate an Executor going offline by killing its process:

```shell script
kill -9 $EXECUTOR_PID # in this case we can see in the logs that it is 19059
```

Then by doing the same check, you can see that the call returns an error:

```json
{"code":1,"description":"failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down.","exception":{"name":"InternalNetworkError","args":["failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down."],"stacks":["Traceback (most recent call last):\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 726, in task_wrapper\n    timeout=timeout,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 241, in send_requests\n    await call_result,\n","  File \"/home/joan/.local/lib/python3.7/site-packages/grpc/aio/_call.py\", line 291, in __await__\n    self._cython_call._status)\n","grpc.aio._call.AioRpcError: <AioRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNAVAILABLE\n\tdetails = \"failed to connect to all addresses\"\n\tdebug_error_string = \"{\"created\":\"@1654074272.702044542\",\"description\":\"Failed to pick subchannel\",\"file\":\"src/core/ext/filters/client_channel/client_channel.cc\",\"file_line\":3134,\"referenced_errors\":[{\"created\":\"@1654074272.702043378\",\"description\":\"failed to connect to all addresses\",\"file\":\"src/core/lib/transport/error_utils.cc\",\"file_line\":163,\"grpc_status\":14}]}\"\n>\n","\nDuring handling of the above exception, another exception occurred:\n\n","Traceback (most recent call last):\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/http/app.py\", line 142, in _flow_health\n    data_type=DataInputType.DOCUMENT,\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/http/app.py\", line 399, in _get_singleton_result\n    async for k in streamer.stream(request_iterator=request_iterator):\n","  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 78, in stream\n    async for response in async_iter:\n","  File \"/home/joan/jina/jina/jina/serve/stream/__init__.py\", line 154, in _stream_requests\n    response = self._result_handler(future.result())\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/request_handling.py\", line 148, in _process_results_at_end_gateway\n    partial_responses = await asyncio.gather(*tasks)\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 128, in _wait_previous_and_send\n    self._handle_internalnetworkerror(err)\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 70, in _handle_internalnetworkerror\n    raise err\n","  File \"/home/joan/jina/jina/jina/serve/runtimes/gateway/graph/topology_graph.py\", line 125, in _wait_previous_and_send\n    timeout=self._timeout_send,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 734, in task_wrapper\n    num_retries=num_retries,\n","  File \"/home/joan/jina/jina/jina/serve/networking.py\", line 697, in _handle_aiorpcerror\n    details=e.details(),\n","jina.excepts.InternalNetworkError: failed to connect to all addresses |Gateway: Communication error with deployment executor0 at address(es) {'0.0.0.0:12346'}. Head or worker(s) may be down.\n"],"executor":""}}
```

(health-check-microservices)=
## Executor health check

You can check every individual Executor in a Flow, by using a [standard gRPC health check endpoint](https://github.com/grpc/grpc/blob/master/doc/health-checking.md).
In most cases this is not necessary, since such checks are performed by Jina, a Kubernetes service mesh or a load balancer under the hood.
Nevertheless, you can perform these checks yourself.

When performing these checks, you can expect one of the following `ServingStatus` responses:
- **`UNKNOWN` (0)**: The health of the Executor could not be determined
- **`SERVING` (1)**: The Executor is healthy and ready to receive requests
- **`NOT_SERVING` (2)**: The Executor is *not* healthy and *not* ready to receive requests
- **`SERVICE_UNKNOWN` (3)**: The health of the Executor could not be determined while performing streaming

````{admonition} See Also
:class: seealso

To learn more about these status codes, and how health checks are performed with gRPC, see [here](https://github.com/grpc/grpc/blob/master/doc/health-checking.md).
````

You can start a Flow inside a terminal and block it to accept requests:

```python
from jina import Flow

f = Flow(protocol='grpc', port=12345).add(port=12346)
with f:
    f.block()
```

In another terminal, you can use [grpcurl](https://github.com/fullstorydev/grpcurl) to send gRPC requests to your services.

```shell
docker pull fullstorydev/grpcurl:latest
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12346 grpc.health.v1.Health/Check
```

```json
{
  "status": "SERVING"
}
```

(health-check-gateway)=
## Gateway health check

Just like each individual Executors, the Gateway also exposes a health check endpoint.

In contrast to Executors however, a Gateway can use gRPC, HTTP, or WebSocketss, and the health check endpoint changes accordingly.


#### Gateway health check with gRPC

When using gRPC as the protocol to communicate with the Gateway, the Gateway uses the exact same mechanism as Executors to expose its health status: It exposes the [standard gRPC health check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) to the outside world.

With the same Flow as before, you can use the same way to check the Gateway status:

```bash
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 grpc.health.v1.Health/Check
```

```json
{
  "status": "SERVING"
}
```


#### Gateway health check with HTTP or WebSockets

````{admonition} Caution
:class: caution
For Gateways running with HTTP or WebSockets, the gRPC health check response codes outlined {ref}`above <health-check-microservices>` do not apply.

Instead, an error free response signifies healthiness.
````

When using HTTP or WebSockets as the protocol for the Gateway, you can query the endpoint `'/'` to check the status.

First, crate a Flow with HTTP or WebSockets protocol:

```python
from jina import Flow

f = Flow(protocol='http', port=12345).add()
with f:
    f.block()
```
Then query the "empty" endpoint:
```bash
curl http://localhost:12345
```

You get a valid empty response indicating the Gateway's ability to serve:
```json
{}
```

## Use jina ping for health checks

Once a Flow is running, you can use `jina ping` CLI  {ref}`CLI <../api/jina_cli>` to run a readiness check of the complete Flow or of individual Executors or Gateway.

Start a Flow in Python:

```python
from jina import Flow

with Flow(protocol='grpc', port=12345).add(port=12346) as f:
    f.block()
```

Check the readiness of the Flow:

```bash
jina ping flow grpc://localhost:12345
```

You can also check the readiness of an Executor:

```bash
jina ping executor localhost:12346
```

...or the readiness of the Gateway service:

```bash
jina ping gateway  grpc://localhost:12345
```

When these commands succeed, you should see something like:

```text
INFO   JINA@28600 readiness check succeeded 1 times!!! 
```

```admonition Use in Kubernetes
:class: note
The CLI exits with code 1 when the readiness check is not successful, which makes it a good choice to be used as readinessProbe for Executor and Gateway when
deployed in Kubernetes.
```
