import os
import time

import pytest
import numpy as np
from jina import Flow, Document

NUM_DOCS = 100
cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
dep_dir = os.path.join(cur_dir, '../../distributed/test_workspaces/')


@pytest.fixture()
def docker_compose(request):
    os.system(f'docker network prune -f ')
    os.system(
        f'docker-compose -f {request.param} --project-directory . up  --build -d --remove-orphans'
    )
    time.sleep(5)
    yield
    os.system(
        f'docker-compose -f {request.param} --project-directory . down --remove-orphans'
    )
    os.system(f'docker network prune -f ')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_upload_simple_non_standard_rootworkspace(docker_compose, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses=os.path.join(dep_dir, 'mwu_encoder.yml'),
            host='localhost:9090',
            upload_files=[os.path.join(dep_dir, 'mwu_encoder.py')],
        )
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()
