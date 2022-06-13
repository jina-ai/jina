import pytest
from docarray import Document, DocumentArray

from jina import Flow


@pytest.mark.parametrize(
    'compression_client', [None, 'NoCompression', 'Gzip', 'Deflate']
)
@pytest.mark.parametrize(
    'compression_gateway', [None, 'NoCompression', 'Gzip', 'Deflate']
)
def test_grpc_compression(compression_client, compression_gateway):
    with Flow(grpc_compression=compression_gateway).add().add() as f:
        ret = f.post(
            on='/',
            inputs=DocumentArray([Document()]),
            grpc_compression=compression_client,
        )
    assert len(ret) == 1


@pytest.mark.parametrize('compression_client', ['A'])
@pytest.mark.parametrize('compression_gateway', ['B'])
def test_grpc_compression_works_with_default(compression_client, compression_gateway):
    with Flow(grpc_compression=compression_gateway).add().add() as f:
        ret = f.post(
            on='/',
            inputs=DocumentArray([Document()]),
            grpc_compression=compression_client,
        )
    assert len(ret) == 1
