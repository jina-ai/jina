#!/usr/bin/env bash

set -e

DOC_DIR=docs

if [[ -z "${1}" ]]; then
    VER_TAG="latest"
else
    VER_TAG=${DRONE_TAG}
fi

cd ${DOC_DIR} && rm -rf api && make clean && pip install -r requirements.txt && cd -

# require docker installed https://github.com/pseudomuto/protoc-gen-doc
docker run --rm \
  -v $(pwd)/docs/chapters/proto:/out \
  -v $(pwd)/jina/proto:/protos \
  pseudomuto/protoc-gen-doc --doc_opt=markdown,docs.md

cd ${DOC_DIR} && make html && cd -


if [ -n "$1" ]; then
    python -m http.server ${1} -d ${DOC_DIR}/_build/html
fi

