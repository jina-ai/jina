(health-check-executor)=
# Health check of an Executor

Executors run as microservices exposing `grpc` endpoints. To give information to the outside world about their health and their readiness to receive requests,
Executors expose a [grpc health check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) service which can be used by different orchestrators like docker-compose, 
or by other services like load-balancers. Jina itself when run locally uses this service to make sure that each Executor is ready to receive traffic.

(##TODO: Maybe add example using grpcurl or something like this)

(health-check-gateway)=
# Health check of the Gateway

The same way individual Executors expose endpoints for orchestrators, clients or other services to check their availability, Gateway as a microservice also exposes this in different ways and depending
on the protocol used.

## Gateway health check with grpc

When using grpc as the protocol used to communicate with the Gateway, then Gateway uses the exact same mechanism as Executors to expose their individual health status. It exposes [grpc health check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) to the outside world.

(##TODO: Maybe add example using grpcurl or something like this)

## Gateway health check with http

## Gateway health check with websocket

# Health check of a Flow exposed to the client
