FROM python:3.7.6-slim

RUN apt-get update && apt-get install --no-install-recommends -y

WORKDIR /builder/

RUN apt-get install --no-install-recommends -y build-essential git automake autoconf libtool wget unzip zlib1g-dev
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.13.0/protoc-3.13.0-linux-x86_64.zip  -O protobuf.zip \
    && unzip protobuf.zip && rm protobuf.zip && \
    cp bin/protoc /usr/local/bin/ && \
    cp -r include/* /usr/local/include/ && \
    git clone --depth 1 https://github.com/grpc/grpc.git && \
    cd grpc && git submodule update --depth 1 --init && \
    make plugins -j 12

WORKDIR /
ADD jina ./jina/

WORKDIR /jina/proto

ENTRYPOINT ["bash", "./build-proto.sh", "/builder/grpc/bins/opt/grpc_python_plugin"]



