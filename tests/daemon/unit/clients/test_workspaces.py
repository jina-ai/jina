import os

from jina import __default_host__
from jina.logging.logger import JinaLogger
from daemon.clients.workspaces import FormData

import aiohttp

logger = JinaLogger('test')
cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_workspace_valid_files():
    executor_directory = '../../../distributed/test_dir_structures/src1'
    with FormData(
        paths=map(lambda p: os.path.join(cur_dir, p), [executor_directory, __file__]),
        logger=logger,
        complete=True,
    ) as data:
        assert isinstance(data, aiohttp.FormData)
        assert len(data) == 2
        assert data.fields[0][0]['name'] == 'files'
        assert data.fields[0][0]['filename'] == 'src1.zip'
        assert data.fields[0][-1].name.endswith('src1.zip')

        assert data.fields[1][0]['name'] == 'files'
        assert data.fields[1][0]['filename'] == os.path.basename(__file__)
        assert data.fields[1][-1].name.endswith('py')


def test_workspace_invalid_files():
    invalid_dirs = ['abc/def', 'abc.py']
    with FormData(paths=invalid_dirs, logger=logger) as data:
        assert isinstance(data, aiohttp.FormData)
        assert len(data) == 0


def test_workspace_none():
    with FormData() as data:
        assert isinstance(data, aiohttp.FormData)
        assert len(data) == 0
