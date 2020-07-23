import os

import numpy as np
from jina.drivers.helper import array2pb
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


def input_fn():
    d = Document()
    d.mime_type = 'text/plain'
    d.blob.CopyFrom(array2pb(np.random.random(7)))
    c = d.chunks.add()
    c.blob.CopyFrom(array2pb(np.random.random(7)))
    yield d
    d = Document()
    d.mime_type = 'image/png'
    d.blob.CopyFrom(array2pb(np.random.random(5)))
    c = d.chunks.add()
    c.blob.CopyFrom(array2pb(np.random.random(5)))
    yield d


class ExcludeQLTestCase(JinaTestCase):

    def test_excludeql_driver(self):
        f = (
            Flow().add(
                name='exclude',
                uses=os.path.join(cur_dir, '../yaml/test-excludeql-driver.yml')))

        def test_excluded(resp):
            for d in resp.docs:
                self.assertFalse(d.HasField('blob'))
                for c in d.chunks:
                    self.assertFalse(c.HasField('buffer'))
                    self.assertFalse(c.HasField('blob'))
                    self.assertFalse(c.HasField('text'))

        with f:
            f.index(input_fn, output_fn=test_excluded, callback_on_body=True)
