#!/bin/bash

CONF_PATH=$(python3 -c "import pkg_resources; print(pkg_resources.resource_filename('jina', 'resources/fluent.conf'))")

# Start fluentd in the background
nohup fluentd -c $CONF_PATH &

# Allowing fluentd conf to load by sleeping for 2secs
sleep 2

# Start jinad (hypercorn) server
python jinad/jinad/main.py
