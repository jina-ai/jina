#!/bin/bash

set -e

# This script fetches the latest protobuf files from the Docarray repository
# and copies them to the `jina-core/proto` directory.

# The script is meant to be run from the root of the repository.

DOCARRAY_VERSION=$1

if [ -z "$DOCARRAY_VERSION" ]; then
    echo "Please provide a Docarray version as the second argument."
    exit 1
fi

if [[ $DOCARRAY_VERSION != "v*" ]]; then
    DOCARRAY_VERSION="v$DOCARRAY_VERSION"
fi

echo "Fetching protos for Docarray version $DOCARRAY_VERSION"
wget https://raw.githubusercontent.com/jina-ai/docarray/$DOCARRAY_VERSION/docarray/proto/docarray.proto -O jina/proto/docarray.proto