#!/usr/bin/env bash

set -ex

rm -rf api && make clean

docker run --rm \
  -v $(pwd)/proto:/out \
  -v $(pwd)/../jina/proto:/protos \
  pseudomuto/protoc-gen-doc --doc_opt=markdown,docs.md

make dirhtml
exit
echo docs.jina.ai > CNAME
git init
git config --local user.email "dev-bot@jina.ai"
git config --local user.name "Jina Dev Bot"
touch .nojekyll
git add .
git commit -m "$2" -a
git status
cd -

