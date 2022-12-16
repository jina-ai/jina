import os

import pytest

from docarray import DocumentArray, Flow

os.environ['JINA_GRPC_SEND_BYTES'] = '0'
os.environ['JINA_GRPC_RECV_BYTES'] = '0'


@pytest.mark.parametrize('inputs', [None, DocumentArray.empty(10)])
def test_grpc_census(inputs):
    assert int(os.environ.get('JINA_GRPC_SEND_BYTES', 0)) == 0
    assert int(os.environ.get('JINA_GRPC_RECV_BYTES', 0)) == 0
    with Flow().add().add() as f:
        f.post(
            on='/',
            inputs=inputs,
        )
    assert int(os.environ['JINA_GRPC_SEND_BYTES']) > 0
    assert int(os.environ['JINA_GRPC_RECV_BYTES']) > 0
    # add some route info, so size must be larger
    assert int(os.environ['JINA_GRPC_SEND_BYTES']) < int(
        os.environ['JINA_GRPC_RECV_BYTES']
    )
    del os.environ['JINA_GRPC_SEND_BYTES']
    del os.environ['JINA_GRPC_RECV_BYTES']
