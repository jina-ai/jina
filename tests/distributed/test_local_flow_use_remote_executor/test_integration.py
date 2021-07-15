import pytest

import numpy as np

from jina import Flow, Document
from jina.parsers import set_pod_parser


@pytest.fixture
def external_pod_args():
    args = [
        '--external',
        '--name',
        'external_fake',
        '--port-in',
        str(45678),
        '--host',
        '52.59.53.88',
        '--host-in',
        '52.59.53.88',
    ]
    args = vars(set_pod_parser().parse_args(args))
    del args['name']
    del args['external']
    del args['pod_role']
    return args


@pytest.fixture
def local_flow(external_pod_args):
    return Flow().add(**external_pod_args, external=True)


@pytest.fixture
def document_to_index():
    image = np.random.random((50, 50))
    return Document(content=image)


def test_local_flow_use_external_executor(local_flow, document_to_index):
    def validate_embedding_shape(resp):
        assert resp.docs[0].blob.shape == (50, 50)
        assert resp.docs[0].embedding.shape == (1024,)

    with local_flow as f:
        f.index(inputs=document_to_index, on_done=validate_embedding_shape)
