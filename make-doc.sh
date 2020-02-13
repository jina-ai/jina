#!/usr/bin/env bash

DOC_DIR=docs

cd ${DOC_DIR} && rm -rf api && make clean && cd -

# require docker installed https://github.com/pseudomuto/protoc-gen-doc
docker run --rm \
  -v $(pwd)/docs/chapters/proto:/out \
  -v $(pwd)/jina/proto:/protos \
  pseudomuto/protoc-gen-doc --doc_opt=markdown,docs.md

cd ${DOC_DIR} && make html && cd -