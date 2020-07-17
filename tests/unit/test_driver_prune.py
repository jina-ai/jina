import numpy as np
import os

from tests import JinaTestCase
from jina.proto.jina_pb2 import Document
from jina.drivers.helper import array2pb
from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def input_fn():
    d = Document()
    d.mime_type = 'text/plain'
    c = d.chunks.add()
    c.blob.CopyFrom(array2pb(np.random.random(7)))
    yield d
    d = Document()
    d.mime_type = 'image/png'
    c = d.chunks.add()
    c.blob.CopyFrom(array2pb(np.random.random(5)))
    yield d


class MyTestCase(JinaTestCase):

    def test_prune_driver(self):
        f = (
            Flow().add(
                name='prune',
                yaml_path=os.path.join(cur_dir, 'yaml/test-prune-driver.yml')))

        def test_pruned(resp):
            for d in resp.docs:
                for c in d.chunks:
                    self.assertFalse(c.HasField('buffer'))
                    self.assertFalse(c.HasField('blob'))
                    self.assertFalse(c.HasField('text'))

        with f:
            f.index(input_fn, output_fn=test_pruned, callback_on_body=True)
