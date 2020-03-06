#!/bin/bash
set -e

# See https://github.com/docker/for-linux/issues/264
if ! host -t A "host.docker.internal" > /dev/null
then
    # Adding host.docker.internal to /etc/hosts"
    ip -4 route list match 0/0 | awk '{print $3 " host.docker.internal"}' >> /etc/hosts
else
    echo "host.docker.internal already defined"
fi

jina "$@"
