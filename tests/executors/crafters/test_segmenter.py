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
    def get_chunk_id(self, req):
        id = 0
        for d in req.index.docs:
            for c in d.chunks:
                self.assertEqual(c.chunk_id, id)
                id += 1

    def collect_chunk_id(self, req):
        chunk_ids = [c.chunk_id for d in req.index.docs for c in d.chunks]
        self.assertTrue(len(chunk_ids), len(set(chunk_ids)))

    def test_dummy_seg(self):
        f = Flow().add(yaml_path='DummySegment')
        with f:
            f.index(input_fn=random_docs(10), output_fn=self.collect_chunk_id)

    def test_dummy_seg_random(self):
        f = Flow().add(yaml_path=os.path.join(cur_dir, '../../yaml/dummy-seg-random.yml'))
        with f:
            f.index(input_fn=random_docs(10), output_fn=self.collect_chunk_id)

    def test_dummy_seg_not_random(self):
        f = Flow().add(yaml_path=os.path.join(cur_dir, '../../yaml/dummy-seg-not-random.yml'))
        with f:
            f.index(input_fn=random_docs(10), output_fn=self.get_chunk_id)
