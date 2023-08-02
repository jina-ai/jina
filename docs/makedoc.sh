#!/usr/bin/env bash

set -ex

if [[ $1 == "local-only" ]]; then 
  rm -rf api && make clean
  cp -r ../jina/proto .
  docker run --rm \
    -v $(pwd)/proto:/out \
    -v $(pwd)/../jina/proto/docarray_v2:/protos \
    ghcr.io/jina-ai/protoc-gen-doc --doc_opt=markdown,docs.md

  make dirhtml
else
  export NUM_RELEASES=${NUM_RELEASES:-10}
  export DEFAULT_BRANCH='master'
  export BUILD_DIR=_build/dirhtml

  declare -a ARR_SMV_TAG_WHITELIST=()
  declare -a ARR_SMV_BRANCH_WHITELIST=()

  rm -rf api && rm -rf ${BUILD_DIR}

  # Might error out with "API Limit exceeds" on local (would need api token), but on CI shouldn't face issues.
  declare -a LAST_N_TAGS=( $(curl -s -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/jina-ai/jina/releases?per_page=${NUM_RELEASES}" \
      | jq -r '.[].tag_name') )

  export LATEST_JINA_VERSION="${LAST_N_TAGS[0]}"

  if [[ $1 == "development" ]]; then
    current_branch=$(git branch --show-current)
    if [[ ${current_branch} != ${DEFAULT_BRANCH} ]]; then
      ARR_SMV_BRANCH_WHITELIST+=" ${current_branch}"
    fi
  fi

  ARR_SMV_BRANCH_WHITELIST+=" ${DEFAULT_BRANCH}"
  ARR_SMV_TAG_WHITELIST+=" ${LAST_N_TAGS[@]}"
  export SMV_BRANCH_WHITELIST="${ARR_SMV_BRANCH_WHITELIST}"
  export SMV_TAG_WHITELIST="${ARR_SMV_TAG_WHITELIST}"

  echo -e "Latest Jina Version: ${LATEST_JINA_VERSION}"
  echo -e "Branches to whitelist: ${SMV_BRANCH_WHITELIST}"
  echo -e "Tags to whitelist: ${SMV_TAG_WHITELIST}"

  docker run --rm \
    -v $(pwd)/proto:/out \
    -v $(pwd)/../jina/proto/docarray_v1:/protos \
    ghcr.io/jina-ai/protoc-gen-doc --doc_opt=markdown,docs.md

  sphinx-multiversion . ${BUILD_DIR} -b dirhtml
  mv -v _build/dirhtml/${LATEST_JINA_VERSION}/* _build/dirhtml
fi
