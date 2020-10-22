#!/usr/bin/env bash
set -e

pip install grpcio
pip install grpcio-tools

SRC_DIR=./
SRC_NAME=jina.proto
VER_FILE=../__init__.py

printf "\e[1;33mgenerating protobuf and grpc python interface\e[0m\n"

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. --mypy_out=. ${SRC_NAME}

printf "\e[1;33mfixing grpc import\e[0m\n"
# fix import bug in google generator
sed -i '' -e '4s/.*/from\ \.\ import\ jina_pb2\ as\ jina__pb2/' ${SRC_DIR}jina_pb2_grpc.py

OLDVER=$(sed -n 's/^__proto_version__ = '\''\(.*\)'\''$/\1/p' $VER_FILE)
printf "current proto version:\t\e[1;33m$OLDVER\e[0m\n"

NEWVER=$(echo $OLDVER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
printf "bump proto version to:\t\e[1;32m$NEWVER\e[0m\n"

sed -i '' -e 's/^__proto_version__ = '\''\(.*\)'\''/__proto_version__ = '\'"$NEWVER"\''/' $VER_FILE
printf "\e[1;32mAll done!\e[0m\n"