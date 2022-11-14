#!/bin/bash
docker build -f Dockerfiles/test-pip.Dockerfile -t jinaai/jina:test-pip .
docker build -t test-executor tests/k8s/test-executor
docker build -t mirror ./mirror