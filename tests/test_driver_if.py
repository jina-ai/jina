from typing import Any

import numpy as np

from jina.drivers.helper import array2pb
from jina.drivers.prune import PruneDriver
from jina.executors import BaseExecutor
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase


class FilterDriver(PruneDriver):
    if_expression = 'doc.doc_id % 2 ==0'

    def __init__(self, pruned=('text',), level='doc', *args, **kwargs):
        super().__init__(pruned, level, *args, **kwargs)


class Encode1(BaseEncoder):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        print('i only encode text/plain')
        return np.random.random([data.shape[0], 3])


class Encode2(BaseEncoder):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        print('i only encode image/png')
        return np.zeros([data.shape[0], 3])


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

    def test_driver_save_load(self):
        id = BaseExecutor.load_config('yaml/test-ifdriver1.yml')
        id.save_config('tmp.yml')
        id = BaseExecutor.load_config('tmp.yml')
        self.assertEqual(id._drivers['IndexRequest'][0].if_expression, '2 > 1')
        self.add_tmpfile('tmp.yml')

    def test_driver_simple_filter(self):
        def validate(req):
            for idx, d in enumerate(req.docs):
                if idx % 2 == 0:
                    self.assertEqual(d.text, '')
                else:
                    self.assertNotEqual(d.text, '')

        f = (Flow().add(yaml_path='yaml/test-ifdriver2.yml'))
        with f:
            f.index_lines(['a', 'b', 'c'], output_fn=validate, callback_on_body=True)

    def test_mime_encode(self):
        # TODO: what is the merge strateg for join() here?
        f = (Flow().add(name='encode1', yaml_path='yaml/test-if-encode1.yml')
             .add(name='encode2', yaml_path='yaml/test-if-encode2.yml', needs='gateway')
             .join(['encode1', 'encode2']))
        with f:
            f.index(input_fn, callback_on_body=True)
