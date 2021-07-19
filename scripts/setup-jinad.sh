#!/bin/bash

set -e

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --debug) debug=true ;;
        -b|--branch) branch="$2"; shift ;;
        -p|--port) port="$2"; shift ;;
        -v|--version) version="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done


echo -e "Executing setup with following args:"
echo -e "debug: ${debug}"
echo -e "branch: ${branch}"
echo -e "port: ${port}"
echo -e "version: ${version}"

if [ -z ${port+x} ]; then
    echo -e "\n'port' is not set. setting it to default (8000)"
    port=8000
fi


if [[ "$debug" = "true" ]]; then
    if [ -z ${branch+x} ]; then
        echo -e "\n'debug' is true, but 'branch' is unset. Exiting!"
        exit 1
    else
        DIR=jina
        if [ -d "$DIR" ]; then
            echo -e "\nremoving jina dir ($DIR)"
            rm -rf "$DIR"
        fi
        echo -e "\n'debug' is true, and 'branch' is set to '${branch}. Building & running jinad!"
        git clone https://github.com/jina-ai/jina.git && cd jina && git fetch && git checkout ${branch}
        docker build -f Dockerfiles/debianx.Dockerfile --build-arg PIP_TAG=daemon -t jinaai/jina:test-daemon .
        docker run --add-host host.docker.internal:host-gateway \
                --name jinad \
                -e JINA_DAEMON_BUILD=DEVEL \
                -e JINA_LOG_LEVEL=DEBUG \
                -v /var/run/docker.sock:/var/run/docker.sock \
                -v /tmp/jinad:/tmp/jinad \
                -p ${port}:8000 \
                --restart unless-stopped \
                -d jinaai/jina:test-daemon
    fi
else
    if [ -z ${version+x} ]; then
        version=latest
    fi
    docker run --add-host host.docker.internal:host-gateway \
            --name jinad \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v /tmp/jinad:/tmp/jinad \
            -p ${port}:8000 \
            --restart unless-stopped \
            -d jinaai/jina:${version}-daemon
fi
