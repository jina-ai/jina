import os
from daemon.stores.workspaces import DaemonFile
from daemon.excepts import Runtime400Exception

import pytest

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    'workdir, expected_response',
    [
        ('good_ws', ('devel', '3.7', '"echo Hello"')),
        ('good_ws_filename', ('gpu', '3.9', '')),
        ('good_ws_nofile', ('devel', '3.8', '')),
        ('good_ws_emptyfile', ('devel', '3.8', '')),
        ('good_ws_multiple_files', ('devel', '3.7', '"echo Hello"')),
        ('good_ws_wrong_values', ('devel', '3.8', '')),
    ],
)
def test_jinad_good_ws(workdir, expected_response):
    d = DaemonFile(workdir=f'{cur_dir}/{workdir}')
    assert d.build == expected_response[0]
    assert d.python == expected_response[1]
    assert d.run == expected_response[2]


@pytest.mark.parametrize('workdir', ['bad_ws_multiple_files'])
def test_jinad_bad_ws(workdir):
    with pytest.raises(Runtime400Exception):
        DaemonFile(workdir=f'{cur_dir}/{workdir}')
