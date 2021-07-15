import os
import time

import pytest
import numpy as np

from jina import Flow, Document
from jina.parsers import set_pod_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')


@pytest.fixture
def external_pod_args():
    args = [
        '--port-in',
        str(45678),
        '--host',
        '172.28.1.1',
        '--host-in',
        '172.28.1.1',
    ]
    args = vars(set_pod_parser().parse_args(args))
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


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_local_flow_use_external_executor(
    local_flow, document_to_index, docker_compose
):
    def validate_embedding_shape(resp):
        print(resp.docs[0])
        assert resp.docs[0].blob.shape == (50, 50)
        assert resp.docs[0].embedding.shape == (512,)

    with local_flow as f:
        f.index(inputs=document_to_index, on_done=validate_embedding_shape)
        # print(rv)
