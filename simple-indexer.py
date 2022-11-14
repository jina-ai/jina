#!python3

import os
import time

from jina import DocumentArray, Flow

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'

flow = Flow(
    tracing=True, traces_exporter_host='localhost', traces_exporter_port=4317
).add(uses="docker://simpleindexer:local", env={'JINA_LOG_LEVEL': 'DEBUG'})

# flow = Flow().add(uses='jinahub+docker://SimpleIndexer')

with flow:
    flow.post("/", DocumentArray.empty())
    # time.sleep(3)
    flow.block()
