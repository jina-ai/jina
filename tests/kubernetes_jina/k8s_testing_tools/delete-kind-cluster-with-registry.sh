#!/bin/sh
kind delete cluster
docker container stop kind-registry
docker rm kind-registry