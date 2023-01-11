#!/bin/bash

set -e

go build
./jraft --raft_id=nodeC --address=localhost:50053 --executor_target=localhost:60063 --raft_data_dir /tmp/jina-raft-cluster