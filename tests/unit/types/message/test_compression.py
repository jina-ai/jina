import pytest

from jina.clients.request import request_generator
from jina.enums import CompressAlgo
from jina.logging.profile import TimeContext
from jina.types.message import Message
from tests import random_docs


@pytest.mark.parametrize('compress_algo', list(CompressAlgo))
@pytest.mark.parametrize('low_bytes', [True, False])
@pytest.mark.parametrize('high_ratio', [False, False])
def test_compression(compress_algo, low_bytes, high_ratio):
    no_comp_sizes = []
    sizes = []
    docs = list(random_docs(100, embed_dim=100))
    kwargs = dict(
        identity='gateway',
        pod_name='123',
        compress_min_bytes=2 * sum(no_comp_sizes) if low_bytes else 0,
        compress_min_ratio=10 if high_ratio else 1,
    )

    with TimeContext(f'no compress'):
        for r in request_generator('/', docs):
            m = Message(None, r, compress=CompressAlgo.NONE, **kwargs)
            m.dump()
            no_comp_sizes.append(m.size)

    kwargs = dict(
        identity='gateway',
        pod_name='123',
        compress_min_bytes=2 * sum(no_comp_sizes) if low_bytes else 0,
        compress_min_ratio=10 if high_ratio else 1,
    )
    with TimeContext(f'compressing with {str(compress_algo)}') as tc:
        for r in request_generator('/', docs):
            m = Message(None, r, compress=compress_algo, **kwargs)
            m.dump()
            sizes.append(m.size)

    if compress_algo == CompressAlgo.NONE or low_bytes or high_ratio:
        assert sum(sizes) >= sum(no_comp_sizes)
    else:
        assert sum(sizes) < sum(no_comp_sizes)
    print(
        f'{str(compress_algo)}: size {sum(sizes) / len(sizes)} (ratio: {sum(no_comp_sizes) / sum(sizes):.2f}) with {tc.duration:.2f}s'
    )
