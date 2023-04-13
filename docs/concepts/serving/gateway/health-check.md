(health-check-gateway)=
# Health Check

Just like each individual Executors, the Gateway also exposes a health check endpoint.

In contrast to Executors however, a Gateway can use gRPC, HTTP, or WebSocketss, and the health check endpoint changes accordingly.


## Using gRPC

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


## Using HTTP or WebSockets

````{admonition} Caution
:class: caution
For Gateways running with HTTP or WebSockets, the gRPC health check response codes outlined {ref}`above <health-check-microservices>` do not apply.

Instead, an error free response signifies healthiness.
````

When using HTTP or WebSockets as the Gateway protocol, you can query the endpoint `'/'` to check the status.

First, create a Flow with HTTP or WebSockets protocol:

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
