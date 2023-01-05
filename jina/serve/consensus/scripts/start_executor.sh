#!/bin/bash

set -e

if [ -z "$1" ];then
    echo "Node name is required as the first argument. Use 'nodeA', 'nodeB' or 'nodeC'"
    exit 1
fi

NODE=$1


BASE_DIRECTORY="/tmp/jina-raft-executor/${NODE}"
mkdir -p $BASE_DIRECTORY
SNAPSHOT_DIRECTORY="${BASE_DIRECTORY}/snapshot"
mkdir -p "${SNAPSHOT_DIRECTORY}"
WORKSPACE="${BASE_DIRECTORY}/workspace"
mkdir -p "${WORKSPACE}"

echo "${SNAPSHOT_DIRECTORY}"
echo "${WORKSPACE}"

export JINA_LOG_LEVEL=DEBUG

set -x
if [ "nodeA" == "${NODE}" ]; then
  ~/.local/bin/jina executor --uses executor/config.yml --port 60061 \
    --snapshot-parent-directory "${SNAPSHOT_DIRECTORY}" --workspace "${WORKSPACE}" --native
elif [ "nodeB" == "${NODE}" ]; then
  ~/.local/bin/jina executor --uses executor/config.yml --port 60062 \
    --snapshot-parent-directory "${SNAPSHOT_DIRECTORY}" --workspace "${WORKSPACE}" --native
elif [ "nodeC" == "${NODE}" ]; then
  ~/.local/bin/jina executor --uses executor/config.yml --port 60063 \
    --snapshot-parent-directory "${SNAPSHOT_DIRECTORY}" --workspace "${WORKSPACE}" --native
else
  echo "Node name is required as the first argument. Use 'nodeA', 'nodeB' or 'nodeC'"
  exit 1
fi

