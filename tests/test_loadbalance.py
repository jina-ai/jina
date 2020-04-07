import os
import time

import numpy as np
from jina.drivers.helper import array2blob
from jina.enums import SchedulerType
from jina.executors.crafters import BaseDocCrafter
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.embedding.CopyFrom(array2blob(np.random.random([embed_dim])))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d


class SlowWorker(BaseDocCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # half of worker is slow
        self.is_slow = os.getpid() % 2 != 0
        self.logger.warning('im a slow worker')

    def craft(self, doc_id, *args, **kwargs):
        if self.is_slow:
            self.logger.warning('slowly doing')
            time.sleep(1)
        return {'doc_id': doc_id}


class MyTestCase(JinaTestCase):
    def test_lb(self):
        f = Flow(runtime='process').add(
            name='sw',
            yaml_path='SlowWorker',
            replicas=10).build()
        with f:
            f.index(raw_bytes=random_docs(100), in_proto=True, batch_size=10)

    def test_roundrobin(self):
        f = Flow(runtime='process').add(
            name='sw',
            yaml_path='SlowWorker',
            replicas=10, scheduling=SchedulerType.ROUND_ROBIN).build()
        with f:
            f.index(raw_bytes=random_docs(100), in_proto=True, batch_size=10)
