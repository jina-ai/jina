import os

import numpy as np
import pytest

from jina import Flow, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('parallels', [1, 2])
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


@pytest.mark.parametrize('parallels', [1, 2])
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
