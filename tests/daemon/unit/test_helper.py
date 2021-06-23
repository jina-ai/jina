import os

from daemon import jinad_args
from daemon.models import DaemonID
from daemon.helper import get_workspace_path


def test_workspace_path():
    uid = DaemonID('jworkspace')
    assert get_workspace_path(uid) == f'{jinad_args.workspace}/{uid}'
    assert get_workspace_path('123', '456') == f'{jinad_args.workspace}/123/456'
