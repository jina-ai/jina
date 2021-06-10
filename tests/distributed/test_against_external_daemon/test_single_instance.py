import os

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
        .add(
            host=CLOUD_HOST,
            parallel=parallels,
            quiet_remote_logs=silent_log,
            timeout_ready=-1,
        )
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
            timeout_ready=120000,
        )
        .add()
    )
    with f:
        f.index(inputs=random_docs(10))
