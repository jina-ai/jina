# {fab}`python` Python API

This section includes the API documentation from the `jina` codebase. These are automatically extracted from the [docstrings](https://peps.python.org/pep-0257/) in the code.


## Client

{class}`~jina.Client`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Convenience function to generate appropriate client object\
{class}`~jina.clients.grpc.GRPCClient`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; gRPC client that can connect to Flow gRPC Gateway\
{class}`~jina.clients.grpc.AsyncGRPCClient`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Asynchronous version of  gRPC client\
{class}`~jina.clients.http.HTTPClient`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; HTTP client that can connect to Flow HTTP Gateway\
{class}`~jina.clients.http.AsyncHTTPClient`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Asynchronous version of HTTP client\
{class}`~jina.clients.websocket.WebSocketClient`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; WebSocket client that can connect to Flow WebSocket Gateway\
{class}`~jina.clients.websocket.AsyncWebSocketClient`&nbsp;&nbsp; Asynchronous version of WebSocket client


## Flow

{class}`~jina.Flow`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Flow connects Executors in a pipeline and exposes API endpoints through a Gateway\
{class}`~jina.orchestrate.flow.asyncio.AsyncFlow`&nbsp;&nbsp; Asynchronous version of the Flow


## Executor

{class}`~jina.Executor`&nbsp;&nbsp; Component that performs operations on DocumentArray\
{class}`~jina.requests`&nbsp;&nbsp; Decorator that creates Executor endpoints\
{class}`~jina.monitor`&nbsp;&nbsp;&nbsp;&nbsp; Decorator and context manager that monitors part of an Executor


## Internals

{class}`~jina.serve.runtimes.asyncio.AsyncNewLoopRuntime`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Base runtime of all Jina components\
{class}`~jina.serve.runtimes.gateway.GatewayRuntime`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Base runtime of all Jina Gateways\
{class}`~jina.serve.runtimes.gateway.grpc.GRPCGatewayRuntime`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; gRPC Gateway runtime\
{class}`~jina.serve.runtimes.gateway.http.HTTPGatewayRuntime`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; HTTP Gateway runtime\
{class}`~jina.serve.runtimes.gateway.websocket.WebSocketGatewayRuntime`&nbsp; WebSocket Gateway runtime\
{class}`~jina.serve.runtimes.worker.WorkerRuntime`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Runtime running an Executor\
{class}`~jina.serve.runtimes.head.HeadRuntime`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Runtime that coordinate shards of an Executor
