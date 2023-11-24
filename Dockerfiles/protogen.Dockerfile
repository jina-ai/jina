FROM --platform=linux/amd64 python:3.7-slim

RUN apt-get update && apt-get install --no-install-recommends -y

WORKDIR /builder/

RUN apt-get install --no-install-recommends -y build-essential git autoconf libtool wget unzip zlib1g-dev pkg-config cmake
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.19.1/protoc-3.19.1-linux-x86_64.zip  -O protobuf.zip \
    && unzip protobuf.zip && rm protobuf.zip && \
    cp bin/protoc /usr/local/bin/ && \
    cp -r include/* /usr/local/include/ && \
    git clone --depth 1 https://github.com/grpc/grpc.git && \
    cd grpc && git submodule update --depth 1 --init && \
    mkdir -p cmake/build && cd cmake/build && cmake ../.. && make -j12

WORKDIR /
ADD jina ./jina/

WORKDIR /jina/proto

ENTRYPOINT ["bash", "./build-proto.sh", "/builder/grpc/cmake/build/grpc_python_plugin", "pb2"]



