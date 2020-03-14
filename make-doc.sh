#!/usr/bin/env bash

set -e

DOC_DIR=docs
HTML_DIR=${DOC_DIR}/_build/html



cd ${DOC_DIR} && rm -rf api && pip install -r requirements.txt && make clean && cd -

# require docker installed https://github.com/pseudomuto/protoc-gen-doc
docker run --rm \
  -v $(pwd)/docs/chapters/proto:/out \
  -v $(pwd)/jina/proto:/protos \
  pseudomuto/protoc-gen-doc --doc_opt=markdown,docs.md

cd ${DOC_DIR} && make html && cd -

if [[ $1 == "commit" ]]; then
  cd ${HTML_DIR}
  git init
  git config --local user.email "dev-team@jina.ai"
  git config --local user.name "Jina Doc Bot"
  git add .
  git commit -m "Docs regular update for ${GITHUB_SHA}" -a
  git status
  cd -
elif [[ $1 == "serve" ]]; then
    python -m http.server $2 -d ${HTML_DIR}
fi

