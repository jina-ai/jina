# Python API

This section includes the API documentation from the `jina` codebase. These are automatically extracted from the [docstrings](https://peps.python.org/pep-0257/) in the code.

## Client
| Class/Function                                        |                                                             |
|-------------------------------------------------------|-------------------------------------------------------------|
| {class}`~jina.Client`                                 | Convenience function to generate appropriate client object  |
| {class}`~jina.clients.grpc.GRPCClient`                | gRPC client that can connect to Flow gRPC Gateway           |
| {class}`~jina.clients.grpc.AsyncGRPCClient`           | Asynchronous version of  gRPC client                        |
| {class}`~jina.clients.http.HTTPClient`                | HTTP client that can connect to Flow HTTP Gateway           |
| {class}`~jina.clients.http.AsyncHTTPClient`           | Asynchronous version of HTTP client                         |
| {class}`~jina.clients.websocket.WebSocketClient`      | WebSocket client that can connect to Flow WebSocket Gateway |
| {class}`~jina.clients.websocket.AsyncWebSocketClient` | Asynchronous version of WebSocket client                    |


## Flow
| Class/Function                                        |                                                                                   |
|-------------------------------------------------------|-----------------------------------------------------------------------------------|
| {class}`~jina.Flow`                                   | Flow connects Executors in a pipeline and exposes API endpoints through a Gateway |
| {class}`~jina.orchestrate.flow.asyncio.AsyncFlow`     | Asynchronous version of the Flow                                                  |

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
