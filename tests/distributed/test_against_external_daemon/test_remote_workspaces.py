import os
import time

import numpy as np
import pytest

from jina import Flow, Client, Document, __default_host__
from ..helpers import create_workspace, wait_for_workspace, delete_workspace

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

"""
Run below commands for local tests
docker build -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .
docker run --add-host host.docker.internal:host-gateway \
    --name jinad -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/jinad:/tmp/jinad \
    -p 8000:8000 -d jinaai/jina:test-daemon
"""

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.mark.parametrize('silent_log', [False])
@pytest.mark.parametrize('parallels', [1])
def test_upload_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses='mwu_encoder.yml',
            host=CLOUD_HOST,
            parallel=parallels,
            upload_files=['mwu_encoder.py'],
            quiet_remote_logs=silent_log,
        )
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [2])
def test_upload_multiple_workspaces(parallels, mocker):
    response_mock = mocker.Mock()
    encoder_workspace = 'tf_encoder_ws'
    indexer_workspace = 'tdb_indexer_ws'

    def _path(dir, filename):
        return os.path.join(cur_dir, dir, filename)

    f = (
        Flow()
        .add(
            name='tf_encoder',
            uses=_path(encoder_workspace, 'tf.yml'),
            host=CLOUD_HOST,
            parallel=parallels,
            py_modules=[_path(encoder_workspace, 'tf_encoder.py')],
            upload_files=[
                _path(encoder_workspace, '.jinad'),
                _path(encoder_workspace, 'requirements.txt'),
            ],
        )
        .add(
            name='tdb_indexer',
            uses=_path(indexer_workspace, 'tdb.yml'),
            host=CLOUD_HOST,
            parallel=parallels,
            py_modules=[_path(indexer_workspace, 'tdb_indexer.py')],
            upload_files=[
                _path(indexer_workspace, '.jinad'),
                _path(indexer_workspace, 'requirements.txt'),
            ],
        )
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


def test_custom_project():

    HOST = __default_host__

    workspace_id = create_workspace(
        dirpath=os.path.join(cur_dir, 'flow_app_ws'), host=HOST
    )
    assert wait_for_workspace(workspace_id, host=HOST)
    # we need to wait for the flow to start in the custom project
    time.sleep(5)

    def gen_docs():
        import string

        d = iter(string.ascii_lowercase)
        while True:
            try:
                yield Document(tags={'first': next(d), 'second': next(d)})
            except StopIteration:
                return

    Client(host=HOST, port_expose=42860, show_progress=True).post(
        on='/index', inputs=gen_docs
    )
    res = Client(host=HOST, port_expose=42860, show_progress=True).post(
        on='/search',
        inputs=Document(tags={'key': 'first', 'value': 's'}),
        return_results=True,
    )
    assert res[0].data.docs[0].matches[0].tags.fields['first'].string_value == 's'
    assert res[0].data.docs[0].matches[0].tags.fields['second'].string_value == 't'
    delete_workspace(workspace_id, host=HOST)


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
            uses='mwu_encoder.yml',
            host='localhost:9000',
            upload_files=['mwu_encoder.py'],
        )
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()
