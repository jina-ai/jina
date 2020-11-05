import os
from typing import List, Dict

import numpy as np
import pytest

from jina.drivers.reduce import CollectEvaluationDriver
from jina.excepts import NoExplicitMessage
from jina.executors import BaseExecutor
from jina.executors.crafters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from jina.logging import default_logger
from jina.proto import jina_pb2
from jina.proto.jina_pb2 import Document, Envelope
from jina.proto.message import ProtoMessage

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
        result.append(r)
    return result


prev_reqs = list(get_prev_reqs())
ev = Envelope()
ev.num_part.extend([1, 3])
prev_msgs = [ProtoMessage(ev, r.SerializeToString(), 'test', 'placeholder') for r in prev_reqs]


class MockCollectEvalDriver(CollectEvaluationDriver):

    @property
    def exec_fn(self):
        return self._exec_fn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._num_call = -1

    @property
    def expect_parts(self) -> int:
        return 3

    @property
    def msg(self) -> 'ProtoMessage':
        r = prev_msgs[self._num_call]
        return r

    @property
    def logger(self) -> 'JinaLogger':
        return default_logger


def test_collect_evals():
    driver = MockCollectEvalDriver()
    executor = BaseExecutor()
    driver.attach(executor=executor, pea=None)
    # before
    for q in prev_reqs:
        assert len(q.index.docs[0].evaluations) == 1

    # reduce to last request, aka current request
    for j in range(2):
        with pytest.raises(NoExplicitMessage):
            driver._num_call += 1
            driver()

    driver._num_call += 1
    driver()

    # after
    assert len(prev_msgs[0].request.docs[0].evaluations) == 1
    assert len(prev_msgs[1].request.docs[0].evaluations) == 1
    assert len(prev_msgs[2].request.docs[0].evaluations) == 3
