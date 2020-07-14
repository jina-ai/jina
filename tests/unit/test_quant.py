import os

import pytest
import numpy as np
from jina.drivers.helper import array2pb, pb2array
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase

replicas = 10

num_docs = 100
chunks_per_doc = 100
embed_dim = 1000


def random_docs():
    c_id = 0
    np.random.seed(531)
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            # force sending at non-quantization
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim]), quantize=None))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d


def get_output(req):
    np.random.seed(531)

    err = 0
    for d in req.docs:
        for c in d.chunks:
            recv = pb2array(c.embedding)
            send = np.random.random([embed_dim])
            err += np.sum(np.abs(recv - send)) / embed_dim

    print(f'reconstruction error: {err / num_docs:.6f}')


class MyTestCase(JinaTestCase):

    def f1(self, quant):
        os.environ['JINA_ARRAY_QUANT'] = quant

        f = Flow(callback_on_body=True).add(yaml_path='_forward').add(yaml_path='_forward').add(
            yaml_path='_forward').add(
            yaml_path='_forward').add(yaml_path='_forward').add(yaml_path='_forward').add(yaml_path='_forward')
        with f as fl:
            fl.index(random_docs, output_fn=get_output)

    def f2(self, quant):
        os.environ['JINA_ARRAY_QUANT'] = quant

        f = Flow(callback_on_body=True, compress_hwm=1024).add(yaml_path='_forward').add(yaml_path='_forward').add(
            yaml_path='_forward').add(
            yaml_path='_forward').add(yaml_path='_forward').add(yaml_path='_forward').add(yaml_path='_forward')
        with f as fl:
            fl.index(random_docs, output_fn=get_output)

    @pytest.mark.skip('this tests hang up for unknown reason on github')
    def test_quant(self):
        for j in ('fp32', 'fp16', 'uint8'):
            self.f1(j)
            self.f2(j)
