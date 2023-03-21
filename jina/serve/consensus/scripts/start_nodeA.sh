#!/bin/bash

set -e

rm -rf /tmp/jina-raft-cluster/node* || echo "Previous cluster workspace doesn't exist."
mkdir -p /tmp/jina-raft-cluster/node{A,B,C}

go build
./jraft --raft_id=nodeA --address=localhost:50051 --executor_target=localhost:60061 --raft_data_dir /tmp/jina-raft-cluster
