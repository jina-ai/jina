import pytest

from jina import Message
from jina.clients.request import _generate
from jina.enums import CompressAlgo
from jina.logging.profile import TimeContext
from tests import random_docs


@pytest.mark.parametrize('compress_algo', list(CompressAlgo))
def test_compression(compress_algo):
    no_comp_sizes = []
    sizes = []
    docs = list(random_docs(10000, embed_dim=100))
    with TimeContext(f'no compress'):
        for r in _generate(docs):
            m = Message(None, r, identity='gateway', pod_name='123', compress=CompressAlgo.NONE)
            m.dump()
            no_comp_sizes.append(m.size)

    with TimeContext(f'compressing with {str(compress_algo)}') as tc:
        for r in _generate(docs):
            m = Message(None, r, identity='gateway', pod_name='123', compress=compress_algo)
            m.dump()
            sizes.append(m.size)
    print(
        f'{str(compress_algo)}: size {sum(sizes) / len(sizes)} ({sum(sizes) / sum(no_comp_sizes):.2f}) with {tc.duration:.2f}s')
