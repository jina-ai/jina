import os
from typing import List, Dict

import numpy as np

from jina.drivers.reduce import CollectEvaluationDriver
from jina.executors import BaseExecutor
from jina.executors.crafters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MockSegmenterReduce(BaseSegmenter):

    def craft(self, text: str, *args, **kwargs) -> List[Dict]:
        split = text.split(',')
        chunks = [dict(text=split[0], offset=0, weight=1.0, modality='mode1'),
                  dict(text=split[1], offset=1, weight=1.0, modality='mode2')]
        return chunks


class MockEncoderReduce(BaseEncoder):

    def encode(self, data: str, *args, **kwargs) -> 'np.ndarray':
        output = []
        for r in data:
            if 'mode1' in r:
                output.append([0.0, 0.0, 0.0])
            elif 'mode2' in r:
                output.append([1.0, 1.0, 1.0])

        return np.array(output)


def test_merge_chunks_with_different_modality():
    def input_fn():
        doc1 = Document()
        doc1.text = 'title: this is mode1 from doc1, body: this is mode2 from doc1'
        doc2 = Document()
        doc2.text = 'title: this is mode1 from doc2, body: this is mode2 from doc2'
        doc3 = Document()
        doc3.text = 'title: this is mode1 from doc3, body: this is mode2 from doc3'
        return [doc1, doc2, doc3]

    def validate(req):
        assert len(req.index.docs) == 3
        for doc in req.index.docs:
            assert len(doc.chunks) == 2
            assert doc.chunks[0].modality in ['mode1', 'mode2']
            assert doc.chunks[1].modality in ['mode1', 'mode2']

    flow = Flow().add(name='crafter', uses='MockSegmenterReduce'). \
        add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml')). \
        add(name='encoder2', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'), needs=['crafter']). \
        add(name='reducer', uses='- !ReduceAllDriver | {traversal_paths: [c]}',
            needs=['encoder1', 'encoder2'])

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate)

def get_prev_reqs():
    # three requests, each with the SAME doc, but diff evaluations
    result = []
    for j in range(3):
        r = jina_pb2.Request()
        d = r.index.docs.add()
        d.id = 'SAME DOC THEY ARE'  # same doc id
        ev1 = d.evaluations.add()
        ev1.value = j  # diff eval
        ev1.op_name = f'op{j}'  # diff eval
        result.append(r.index)
    return result

prev_reqs = get_prev_reqs()

class MockCollectEvalDriver(CollectEvaluationDriver):

    @property
    def exec_fn(self):
        return self._exec_fn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def prev_reqs(self):
        # generate it before hand, and make it mutable
        return prev_reqs


def test_collect_evals():
    driver = MockCollectEvalDriver()
    executor = BaseExecutor()
    driver.attach(executor=executor, pea=None)
    # before
    for q in driver.prev_reqs:
        assert len(q.docs[0].evaluations) == 1

    # reduce to last request, aka current request
    driver.reduce()

    # after
    assert len(driver.prev_reqs[0].docs[0].evaluations) == 1
    assert len(driver.prev_reqs[1].docs[0].evaluations) == 1
    assert len(driver.prev_reqs[2].docs[0].evaluations) == 3

