#!/bin/bash

set -e

raftadmin localhost:61177 add_voter 1 localhost:62494 0
raftadmin localhost:61177 add_voter 2 localhost:56601 0
#raftadmin --leader multi:///localhost:50051,localhost:50052 add_voter nodeC localhost:50053 0