#!/bin/bash

set -e

raftadmin localhost:51944 add_voter 1 localhost:57673 0
raftadmin localhost:51944 add_voter 2 localhost:65499 0
#raftadmin --leader multi:///localhost:50051,localhost:50052 add_voter nodeC localhost:50053 0