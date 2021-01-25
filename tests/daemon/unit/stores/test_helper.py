import os

from daemon import jinad_args
from daemon.stores.helper import get_workspace_path, jina_workspace
from jina.helper import random_uuid


def test_workspace_path():
    uid = random_uuid()
    assert get_workspace_path(uid) == f'{jinad_args.workspace}/{uid}'
    assert get_workspace_path('123', '456') == f'{jinad_args.workspace}/123/456'


def test_jina_workspace():
    uid = random_uuid()
    assert 'JINA_LOG_WORKSPACE' not in os.environ
    assert not os.path.exists(get_workspace_path(uid))
    with jina_workspace(uid):
        assert os.path.exists(get_workspace_path(uid))
        assert get_workspace_path(uid) in os.getcwd()
        assert 'JINA_LOG_WORKSPACE' in os.environ
        assert os.environ['JINA_LOG_WORKSPACE'] in os.getcwd()

    assert 'JINA_LOG_WORKSPACE' not in os.environ
