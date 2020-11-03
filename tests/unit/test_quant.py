import os

import numpy as np
import pytest

from jina.flow import Flow
from jina.proto.ndarray.generic import GenericNdArray
from tests import random_docs

parallel = 10

num_docs = 100
chunks_per_doc = 100
embed_dim = 1000
rseed = 531


def get_output(req):
    np.random.seed(rseed)

    err = 0
    for d in req.docs:
        recv = GenericNdArray(d.embedding).value
        send = np.random.random([embed_dim])
        err += np.sum(np.abs(recv - send)) / embed_dim
        for c in d.chunks:
            recv = GenericNdArray(c.embedding).value
            send = np.random.random([embed_dim])
            err += np.sum(np.abs(recv - send)) / embed_dim

    print(f'reconstruction error: {err / num_docs:.6f}')


@pytest.mark.parametrize('quant', ['fp32', 'fp16', 'uint8'])
def test_quant_f1(quant):
    np.random.seed(rseed)
    os.environ['JINA_ARRAY_QUANT'] = quant

    f = Flow(callback_on_body=True).add(uses='_pass')
    with f as fl:
        fl.index(random_docs(num_docs, chunks_per_doc=chunks_per_doc, embed_dim=embed_dim), output_fn=get_output)


@pytest.mark.parametrize('quant', ['fp32', 'fp16', 'uint8'])
def test_quant_f2(quant):
    np.random.seed(rseed)
    os.environ['JINA_ARRAY_QUANT'] = quant

    f = Flow(callback_on_body=True).add(uses='_pass')
    with f as fl:
        fl.index(random_docs(num_docs, chunks_per_doc=chunks_per_doc, embed_dim=embed_dim), output_fn=get_output)
