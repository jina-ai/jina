import os

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_docs(num_docs):
    for j in range(num_docs):
        yield jina_pb2.Document()


class DummySegment(BaseSegmenter):
    def craft(self):
        return [dict(buffer=b'aa'), dict(buffer=b'bb')]


class MyTestCase(JinaTestCase):
    def validate(self, req):
        chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
        self.assertTrue(len(chunk_ids), len(set(chunk_ids)))
        self.assertTrue(len(chunk_ids), 2)

    def test_dummy_seg(self):
        f = Flow().add(uses='DummySegment')
        with f:
            f.index(input_fn=random_docs(10), output_fn=self.validate)

    def test_dummy_seg_random(self):
        f = Flow().add(uses=os.path.join(cur_dir, '../../yaml/dummy-seg-random.yml'))
        with f:
            f.index(input_fn=random_docs(10), output_fn=self.validate)

    def test_dummy_seg_not_random(self):
        f = Flow().add(uses=os.path.join(cur_dir, '../../yaml/dummy-seg-not-random.yml'))
        with f:
            f.index(input_fn=random_docs(10), output_fn=self.validate)
