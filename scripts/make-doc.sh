#!/usr/bin/env bash

set -ex

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
  cd ${DOC_DIR}
  cp README.md jinahub.jpg jina-logo-dark.png _build/html/
  cd -
  cd ${HTML_DIR}
  rsync -avr . master  # sync to master/
  rsync -avr --exclude=master . ${JINA_VERSION}  # sync to version/
  echo docs.jina.ai > CNAME
  git init
  git config --local user.email "dev-bot@jina.ai"
  git config --local user.name "Jina Dev Bot"
  touch .nojekyll
  git add .
  git commit -m "$2" -a
  git status
  cd -
elif [[ $1 == "release" ]]; then
  cd ${DOC_DIR}
  cp README.md jinahub.jpg jina-logo-dark.png _build/html/
  cd -
  cd ${HTML_DIR}
  rsync -avr . latest  # sync to latest/
  rsync -avr --exclude=latest . ${JINA_VERSION}  # sync to versions
  echo docs.jina.ai > CNAME
  git init
  git config --local user.email "dev-bot@jina.ai"
  git config --local user.name "Jina Dev Bot"
  touch .nojekyll
  git add .
  git commit -m "$2" -a   # commit before tagging, otherwise throw fatal: Failed to resolve 'HEAD' as a valid ref.
  git tag ${V_JINA_VERSION}
  git status
  cd -
elif [[ $1 == "serve" ]]; then
    python -m http.server $2 -d ${HTML_DIR}
fi

