#!/usr/bin/env bash
set -ex

# Do NOT use this directly, use jinaai/protogen image
#
# current dir: docarray root (the one with README.md)
# run the following in bash:
# docker run -v $(pwd)/proto:/jina/proto jinaai/protogen

SRC_DIR=./
SRC_NAME=docarray.proto
VER_FILE=../__init__.py

if [ "$#" -ne 1 ]; then
    echo "Error: Please specify the [PATH_TO_GRPC_PYTHON_PLUGIN], refer more details at " \
      "https://docs.jina.ai/"
    printf "\n"
    echo "USAGE:"
    printf "\t"
    echo "bash ./build-proto.sh [PATH_TO_GRPC_PYTHON_PLUGIN]"
    exit 1
fi

PLUGIN_PATH=${1}  # /Volumes/TOSHIBA-4T/Documents/grpc/bins/opt/grpc_python_plugin

printf "\e[1;33mgenerating protobuf and grpc python interface\e[0m\n"

protoc -I ${SRC_DIR} --python_out=${SRC_DIR} ${SRC_DIR}${SRC_NAME}