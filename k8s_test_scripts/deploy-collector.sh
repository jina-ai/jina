#!/bin/bash
kubectl apply -f test_stuff/dep/namespace.yml
kubectl apply -Rf test_stuff/dep --namespace meow
kubectl get all --namespace meow