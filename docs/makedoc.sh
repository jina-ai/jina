#!/usr/bin/env bash

set -ex

rm -rf api && make clean

docker run --rm \
  -v $(pwd)/proto:/out \
  -v $(pwd)/../jina/proto:/protos \
  pseudomuto/protoc-gen-doc --doc_opt=markdown,docs.md

make dirhtml