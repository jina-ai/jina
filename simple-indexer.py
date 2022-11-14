#!python3

import os
import time

from jina import DocumentArray, Flow

os.environ['JINA_VCS_VERSION'] = 'a8b9c44aa0b6d778beff159fbd315153b76feb2b'

flow = Flow(
    tracing=True, traces_exporter_host='localhost', traces_exporter_port=4317
).add(uses="docker://simpleindexer:local")

# flow = Flow().add(uses='jinahub+docker://SimpleIndexer')

with flow:
    flow.post("/", DocumentArray.empty())
    # time.sleep(3)
    flow.block()
