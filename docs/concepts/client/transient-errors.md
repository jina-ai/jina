(transient-erros)=

# Transient Errors

Most transient errors can be attributed to network issues between the client and target server or between a server's
dependencies like a database. The errors can be:

1. ignored if an operation produced by a generator or sequence of operations isn't relevant to the overall success.
2. retried up to a certain limit which assumes that the recovery logic kicks in to repair transient errors.
3. accept that the operation cannot be successfully completed.

The following sections describe the various features that can be used to handle one or more of the above listed
scenarios.

## Transient fault handling with retries

The {meth}`~jina.clients.mixin.PostMixin.post` method accepts `max_attempts`, `initial_backoff`, `max_backoff`
and `backoff_multiplier` parameters to control the capacity to retry requests when a transient connectivity error
occurs, using an exponential backoff strategy.
This can help to overcome transient network connectivity issues which are broadly captured by the
{class}`~grpc.aio.AioRpcError`, {class}`~asyncio.CancelledError` and {class}`~jina.excepts.InternalNetworkError`
exception types.

The `max_attempts` parameter determines the number of sending attempts, including the original request.
The `initial_backoff`, `max_backoff`, and `backoff_multiplier` parameters determine the randomized delay in seconds
before retry attempts.

The initial retry attempt will occur at `initial_backoff`. In general, the *n-th* attempt will occur
at `random(0, min(initial_backoff*backoff_multiplier**(n-1), max_backoff))`.

### Handling gRPC retries for streaming and unary RPC methods

The {meth}`~jina.clients.mixin.PostMixin.post` method supports the `stream` boolean parameter. If set to `True`,
the **gRPC** server side streaming RPC method will be invoked. If set to `False`, the server side unary RPC method will
be invoked. Some important implication of
using retries with **gRPC** are:

1. The built-in **gRPC** retries are limited in scope and are implemented to work under certain circumstances. More
   details are specified in the [design document](https://github.com/grpc/proposal/blob/master/A6-client-retries.md).
2. If `stream` parameter is set to True (defaults to True), the retry must
   be handled as below because the result must be consumed to check for errors in the stream of responses.

   ```python
   from jina import Client, DocumentArray
   from jina.clients.base.retry import wait_or_raise_err
   from jina.helper import run_async

   client = Client(host='grpc://localhost:12345')

   max_attempts = 5
   initial_backoff = 0.8
   backoff_multiplier = 1.5
   max_backoff = 5

   for attempt in range(1, max_attempts + 1):
       try:
           response = client.post(
               '/',
               inputs=DocumentArray.empty(2),
               request_size=1,
               timeout=0.5,
           )
           assert len(response) == 1
       except ConnectionError as err:
           run_async(
               wait_or_raise_err,
               attempt=attempt,
               err=err,
               max_attempts=max_attempts,
               backoff_multiplier=backoff_multiplier,
               initial_backoff=initial_backoff,
               max_backoff=max_backoff,
           )
   ```

3. If the `stream` parameter is set to False, the {meth}`~jina.clients.mixin.PostMixin.post` method invokes the unary
   RPC method and the
   retry is handled internally based on the `max_attempts`, `initial_backoff`, `backoff_multiplier` and `max_backoff`
   parameters.

```{hint}
The retry parameters `max_attempts`, `initial_backoff`, `backoff_multiplier` and `max_backoff` of the {meth}`~jina.clients.mixin.PostMixin.post` method will be used to set the **gRPC** retry service options. This improves the chances of success if the gRPC retry conditions are met.
```

## Continue streaming when an Executor error occurs

The {meth}`~jina.clients.mixin.PostMixin.post` accepts a `continue_on_error` parameter. When set to `True`, the Client
will keep trying to send the remaining requests. The `continue_on_error` parameter will only apply
to Exceptions caused by an Executor, but in case of network connectivity issues, an Exception will be raised.

## Retries with a large inputs or long-running operations

When using the gRPC client, it is recommended to set the `stream` parameter to False so that the unary RPC is invoked by
the {class}`~jina.Client`
which performs the retry internally with the request from the `inputs` iterator or generator. The `request_size`
parameter must also be set to perform smaller operations which can be retried without much overhead on the server.

The **HTTP** and **WebSocket**

```{hint}
Refer to {ref}`Callbacks <callback-functions>` section for dealing with success and failures after retries.
```