#Build add_voter proto

ina support two versions of protobuf, before 3.19 and after (which is a breaking change for python), therefore we have
duplicate python file generation from proto based on the installed protobuf version.)

This complex setup lead to a not straightforward way to generate the python code from the proto

this guide explain how to do it properly.

# how to build the proto

## 1. build docker image for protobuf generation


``` cmd
docker build -f Dockerfiles/protogen.Dockerfile -t jinaai/protogen:local .
```

This build the docker image that will be used to generate the python code from the proto for proto **before** 3.19

``` cmd
docker build -f Dockerfiles/protogen-3.21.Dockerfile -t jinaai/protogen-3.21:local .
```

This build the docker image that will be used to generate the python code from the proto for proto **after* 3.19

## 2. generate the python code from the proto

note: you need to be in the root of the repo to do the following steps


``` cmd
docker run -it -v $(pwd)/jina/serve/consensus/add_voter:/jina/serve/consensus/add_voter --entrypoint=/bin/bash jinaai/protogen:local
cd /jina/serve/consensus/add_voter
bash build-add-voter-proto.sh /builder/grpc/cmake/build/grpc_python_plugin pb2
```

``` 
docker run -it -v $(pwd)/jina/serve/consensus/add_voter:/jina/serve/consensus/add_voter --entrypoint=/bin/bash jinaai/protogen-3.21:local
cd /jina/serve/consensus/add_voter
bash build-add-voter-proto.sh /builder/grpc/cmake/build/grpc_python_plugin pb
```