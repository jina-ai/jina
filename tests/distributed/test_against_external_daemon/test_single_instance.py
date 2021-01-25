import os

import numpy as np
import pytest

from jina import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()
    f = (Flow()
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         .add(parallel=parallels))
    with f:
        f.index(('hello' for _ in range(NUM_DOCS)), on_done=response_mock)

    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (Flow()
         .add(parallel=parallels)
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         )
    with f:
        f.index(('hello' for _ in range(NUM_DOCS)), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_r_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (Flow()
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         .add()
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         )
    with f:
        f.index(('hello' for _ in range(NUM_DOCS)), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_r_r_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (Flow()
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         )
    with f:
        f.index(('hello' for _ in range(NUM_DOCS)), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_l_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()

    f = (Flow()
         .add()
         .add(host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log)
         .add()
         )
    with f:
        f.index(('hello' for _ in range(NUM_DOCS)), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_l_with_upload(silent_log, parallels, mocker):
    response_mock = mocker.Mock()
    f = (Flow()
         .add()
         .add(uses='mwu_encoder.yml',
              host=CLOUD_HOST,
              parallel=parallels,
              upload_files=['mwu_encoder.py'],
              silent_remote_logs=silent_log)
         .add())
    with f:
        f.index_ndarray(np.random.random([NUM_DOCS, 100]), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1])  # TODO: parallel > 1 fails, need to check if local also work
def test_l_r_l_with_upload(silent_log, parallels, mocker):
    img_name = 'test-mwu-encoder'
    import docker
    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, '../../unit/mwu-encoder/'), tag=img_name)
    client.close()

    response_mock = mocker.Mock()
    f = (Flow()
         .add()
         .add(uses=f'docker://{img_name}',
              host=CLOUD_HOST,
              parallel=parallels,
              silent_remote_logs=silent_log,
              pull_latest=True,
              timeout_ready=60000,
              entrypoint='jina pea')
         .add())
    with f:
        f.index_ndarray(np.random.random([NUM_DOCS, 100]), on_done=response_mock)
    response_mock.assert_called()

    client = docker.from_env()
    client.containers.prune()
