#!/usr/bin/env bash

declare -r cmd_arg=$1

if [[ $cmd_arg == "master" ]]; then
  jina_version="master"
else
  jina_version=$(git ls-remote --tags https://github.com/jina-ai/jina.git "refs/tags/v*^{}" | cut -d'/' -f3 | cut -d'^' -f1 | cut -d'v' -f2 | sort -Vr | head -n $cmd_arg | tail -n 1)
fi

docker build --build-arg JINA_VER=$jina_version -f Dockerfile -t latency-tracking .
docker run -v /var/output:/app/output latency-tracking