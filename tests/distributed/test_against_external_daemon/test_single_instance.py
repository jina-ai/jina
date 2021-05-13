import os

import numpy as np
import pytest

from jina import Flow, Document
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
        .add(parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )

    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(parallel=parallels)
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_r_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
        .add()
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_r_r_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_l_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add()
        .add(host=CLOUD_HOST, parallel=parallels, quiet_remote_logs=silent_log)
        .add()
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_l_with_upload(silent_log, parallels, mocker):
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


@pytest.fixture()
def docker_image():
    img_name = 'test-mwu-encoder'
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, '../../unit/mwu-encoder/'), tag=img_name
    )
    client.close()
    yield img_name
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2, 3])
def test_l_r_l_with_upload_remote(silent_log, parallels, docker_image, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses=f'docker://{docker_image}',
            host=CLOUD_HOST,
            parallel=parallels,
            quiet_remote_logs=silent_log,
            timeout_ready=60000,
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
def test_create_pea_timeout(parallels):
    f = (
        Flow()
        .add()
        .add(
            uses='delayed_executor.yml',
            host=CLOUD_HOST,
            parallel=parallels,
            upload_files=['delayed_executor.py'],
            timeout_ready=20000,
        )
        .add()
    )
    with f:
        f.index(inputs=random_docs(10))
