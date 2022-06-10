# Python API

This section includes the API documentation from the `jina` codebase. These are automatically extracted from the [docstrings](https://peps.python.org/pep-0257/) in the code.

## Client
| Class/Function                                        |                                                |
|-------------------------------------------------------|------------------------------------------------|
| {class}`~jina.Client`                                 | Function to generate appropriate client object |
| {class}`~jina.clients.grpc.GRPCClient`                | gRPC client                                    |
| {class}`~jina.clients.grpc.AsyncGRPCClient`           | Asynchronous gRPC client                       |
| {class}`~jina.clients.http.HTTPClient`                | HTTP client                                    |
| {class}`~jina.clients.http.AsyncHTTPClient`           | Asynchronous HTTP client                       |
| {class}`~jina.clients.websocket.WebSocketClient`      | WebSocket client                               |
| {class}`~jina.clients.websocket.AsyncWebSocketClient` | Asynchronous WebSocket client                  |


## Flow
| Class/Function                                        |                                     |
|-------------------------------------------------------|-------------------------------------|
| {class}`~jina.Flow`                                   | Flow orchestrates Executors         |
| {class}`~jina.orchestrate.flow.asyncio.AsyncFlow`     | Flow with an asynchronous interface |

## Executor
| Class/Function          |                                                                 |
|-------------------------|-----------------------------------------------------------------|
| {class}`~jina.Executor` | Component that performs operations on DocumentArray             |
| {class}`~jina.requests` | Decorator that creates Executor endpoints                       |
| {class}`~jina.monitor`  | Decorator and context manager that monitors part of an Executor |


## Internals
| Class/Function                                                          |                                               |
|-------------------------------------------------------------------------|-----------------------------------------------|
| {class}`~jina.serve.runtimes.asyncio.AsyncNewLoopRuntime`               | Base runtime of all Jina components           |
| {class}`~jina.serve.runtimes.gateway.GatewayRuntime`                    | Base runtime of all Jina Gateways             |
| {class}`~jina.serve.runtimes.gateway.grpc.GRPCGatewayRuntime`           | gRPC Gateway runtime                          |
| {class}`~jina.serve.runtimes.gateway.http.HTTPGatewayRuntime`           | HTTP Gateway runtime                          |
| {class}`~jina.serve.runtimes.gateway.websocket.WebSocketGatewayRuntime` | WebSocket Gateway runtime                     |
| {class}`~jina.serve.runtimes.worker.WorkerRuntime`                      | Runtime running an Executor                   |
| {class}`~jina.serve.runtimes.head.HeadRuntime`                          | Runtime that coordinate shards of an Executor |
