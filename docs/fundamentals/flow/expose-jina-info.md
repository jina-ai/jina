# Expose Information on microservices
Every Jina Flow consists of a {ref}`number of microservices <architecture-overview>`,
each of which may live in different environments, and even run different Jina versions.

```{warning} Use same jina version
Even though you can theoretically run Executors and Gateways in different Jina versions, it is recommended for them to work with the same Jina version, and the same as the client used to interact with them.
```

Each Flow microservice provides an endpoint that exposes relevant information about the environment where it runs. 

This information exposes information in a dict-like structure with the following keys:
- jina: A dictionary containing information about the system and the versions of several packages including jina package itself
- envs: A dictionary containing all the values if set of the {ref}`environment variables used in Jina <jina-env-vars>`


## Access Information of GRPC-based microservices

To access this information for any of the GRPC-based microservices of Jina (Executors or Gateway using grpc protocol) you can use any grpc client.

To see how this works, first instantiate a Flow with an Executor exposed to an specific port and block it for serving:

```python
from jina import Flow

PROTOCOL = 'grpc'  # it could also be http or websocket

with Flow(protocol=PROTOCOL, port=12345).add() as f:
    f.block()
```

Then, you can use [grpcurl](https://github.com/fullstorydev/grpcurl) to hit the gRPC service

```shell
docker pull fullstorydev/grpcurl:latest
docker run --network='host' fullstorydev/grpcurl -plaintext 127.0.0.1:12345 jina.JinaInfoRPC/_status
```
The error-free output below signifies a correctly running Flow:
```text
{
  "jina": {
    "architecture": "######",
    "ci-vendor": "######",
    "docarray": "######",
    "grpcio": "######",
    "jina": "######",
    "jina-proto": "######",
    "jina-vcs-tag": "######",
    "platform": "######",
    "platform-release": "######",
    "platform-version": "######",
    "processor": "######",
    "proto-backend": "######",
    "protobuf": ""######",
    "python": "######", 
    "pyyaml": "######",
    "session-id": "######",
    "uid": "######",
    "uptime": "######",
  },
  "envs": {
    "JINA_AUTH_TOKEN": "(unset)",
    "JINA_DEFAULT_HOST": "(unset)",
    "JINA_DEFAULT_TIMEOUT_CTRL": "(unset)",
    "JINA_DEFAULT_WORKSPACE_BASE": "#####",
    "JINA_DEPLOYMENT_NAME": "(unset)",
    "JINA_DISABLE_HEALTHCHECK_LOGS": "(unset)",
    "JINA_DISABLE_UVLOOP": "(unset)",
    "JINA_EARLY_STOP": "(unset)",
    "JINA_FULL_CLI": "(unset)",
    "JINA_GATEWAY_IMAGE": "(unset)",
    "JINA_GRPC_RECV_BYTES": "(unset)",
    "JINA_GRPC_SEND_BYTES": "(unset)",
    "JINA_HUBBLE_REGISTRY": "(unset)",
    "JINA_HUB_CACHE_DIR": "(unset)",
    "JINA_HUB_NO_IMAGE_REBUILD": "(unset)",
    "JINA_HUB_ROOT": "(unset)",
    "JINA_LOCKS_ROOT": "(unset)",
    "JINA_LOG_CONFIG": "(unset)",
    "JINA_LOG_LEVEL": "(unset)",
    "JINA_LOG_NO_COLOR": "(unset)",
    "JINA_MP_START_METHOD": "(unset)",
    "JINA_RANDOM_PORT_MAX": "(unset)",
    "JINA_RANDOM_PORT_MIN": "(unset)",
  }
}
```

## Access Information of Gateway using HTTP/Websocket protocol

When using HTTP or Websocket as the Gateway protocol, you can use curl to target the `/status` endpoint and get the Jina info.

```shell
curl http://localhost:12345/status
```

```text
{"jina":{"jina":"######","docarray":"######","jina-proto":"######","jina-vcs-tag":"(unset)","protobuf":"######","proto-backend":"######","grpcio":"######","pyyaml":"######","python":"######","platform":"######","platform-release":"######","platform-version":"######","architecture":"######","processor":"######","uid":"######","session-id":"######","uptime":"######","ci-vendor":"(unset)"},"envs":{"JINA_AUTH_TOKEN":"(unset)","JINA_DEFAULT_HOST":"(unset)","JINA_DEFAULT_TIMEOUT_CTRL":"(unset)","JINA_DEFAULT_WORKSPACE_BASE":"######","JINA_DEPLOYMENT_NAME":"(unset)","JINA_DISABLE_UVLOOP":"(unset)","JINA_EARLY_STOP":"(unset)","JINA_FULL_CLI":"(unset)","JINA_GATEWAY_IMAGE":"(unset)","JINA_GRPC_RECV_BYTES":"(unset)","JINA_GRPC_SEND_BYTES":"(unset)","JINA_HUBBLE_REGISTRY":"(unset)","JINA_HUB_CACHE_DIR":"(unset)","JINA_HUB_NO_IMAGE_REBUILD":"(unset)","JINA_HUB_ROOT":"(unset)","JINA_LOG_CONFIG":"(unset)","JINA_LOG_LEVEL":"(unset)","JINA_LOG_NO_COLOR":"(unset)","JINA_MP_START_METHOD":"(unset)","JINA_RANDOM_PORT_MAX":"(unset)","JINA_RANDOM_PORT_MIN":"(unset)","JINA_DISABLE_HEALTHCHECK_LOGS":"(unset)","JINA_LOCKS_ROOT":"(unset)"}}%
```
