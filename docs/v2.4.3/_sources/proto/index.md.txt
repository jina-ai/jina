# Jina Protobuf Specification


For developers who want to change the protobuf specification, one needs to first edit `jina/proto/jina.proto` and then use `jina/proto/build-proto.sh` to regenerate the python interfaces (i.e. `jina/proto/jina_pb2.py` and `jina/proto/jina_pb2_grpc.py`).

````{tip}
We provide a Docker image for you to generate Protobuf interface in the containerized environment. That means you don't need to config the build protobuf/grpc environment locally. Simply use 

```bash
docker run -v $(pwd)/jina/proto:/jina/proto jinaai/protogen
```
where `$(pwd)` is your Jina repository root.

````


```{toctree}
:hidden:

docs
```
