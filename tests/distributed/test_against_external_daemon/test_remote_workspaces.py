import os
import time

import numpy as np
import pytest

from jina import Flow, Client, Document
from ..helpers import create_workspace, wait_for_workspace, delete_workspace

cur_dir = os.path.dirname(os.path.abspath(__file__))

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


@pytest.mark.parametrize('parallels', [1])
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


def test_custom_project(mocker):
    response_mock = mocker.Mock()

    workspace_id = create_workspace(dirpath=os.path.join(cur_dir, 'flow_app_ws'))
    # we need to wait for the flow to start in the custom project
    time.sleep(5.0)
    assert wait_for_workspace(workspace_id)
    Client(host='0.0.0.0', port_expose=42860, show_progress=True).index(
        inputs=(Document(text='hello') for _ in range(NUM_DOCS)), on_done=response_mock
    )
    response_mock.assert_called()
    delete_workspace(workspace_id)
