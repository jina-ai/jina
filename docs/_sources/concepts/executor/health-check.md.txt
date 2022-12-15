(health-check-microservices)=
# Health Check

You can check every individual Executor, by using a [standard gRPC health check endpoint](https://github.com/grpc/grpc/blob/master/doc/health-checking.md).
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

```python
MyExec.serve(port=12346)
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
