#!/bin/bash

set -e 

raftadmin --leader multi:///localhost:50051,localhost:50052,localhost:50053 snapshot