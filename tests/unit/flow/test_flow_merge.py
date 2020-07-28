import os

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase, random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))
import random


def random_docs(num_docs):
    for j in range(num_docs):
        yield jina_pb2.Document()


class DummySegment(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = random.random()

    def craft(self):
        return [dict(buffer=f'aa{self._label}'.encode()), dict(buffer=f'bb{self._label}'.encode())]


class MyTestCase(JinaTestCase):
    def validate(self, req):
        chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
        self.assertTrue(len(chunk_ids), len(set(chunk_ids)))
        self.assertTrue(len(chunk_ids), 2)

    def test_dummy_seg(self):
        f = (Flow().add(name='a11', uses='DummySegment')
             .add(name='a12', uses='DummySegment', needs='gateway')
             .add(name='r1', uses='_merge_all', needs=['a11', 'a12'])
             .add(name='a21', uses='DummySegment', needs='gateway')
             .add(name='a22', uses='DummySegment', needs='gateway')
             .add(name='r2', uses='_merge_all', needs=['a21', 'a22'])
             .add(uses='_merge_all', needs=['r1', 'r2']))

        with f:
            f.index(input_fn=random_docs(10), output_fn=self.validate)
