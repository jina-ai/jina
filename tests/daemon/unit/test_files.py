import os

from jina.excepts import DaemonInvalidDockerfile
from daemon import daemon_logger
from daemon.files import DaemonFile, is_requirements_txt

import pytest

cur_dir = os.path.dirname(os.path.abspath(__file__))
cur_filename = os.path.basename(__file__)


@pytest.mark.parametrize(
    'workdir, expected_response',
    [
        (
            'good_ws',
            (
                os.path.join('daemon', 'Dockerfiles', 'default.Dockerfile'),
                '3.7',
                'echo Hello',
                [12345, 12344],
            ),
        ),
        (
            'good_ws_no_file',
            (
                os.path.join('daemon', 'Dockerfiles', 'devel.Dockerfile'),
                '3.8',
                '',
                [],
            ),
        ),
        (
            'good_ws_emptyfile',
            (os.path.join('daemon', 'Dockerfiles', 'devel.Dockerfile'), '3.8', '', []),
        ),
        (
            'good_ws_multiple_files',
            (
                os.path.join('daemon', 'Dockerfiles', 'devel.Dockerfile'),
                '3.7',
                'echo Hello',
                [12345, 123456],
            ),
        ),
        (
            'good_ws_wrong_ports',
            (
                os.path.join('daemon', 'Dockerfiles', 'devel.Dockerfile'),
                '3.8',
                '',
                [],
            ),
        ),
        (
            'good_ws_custom_dockerfile',
            (
                os.path.join(
                    'models', 'good_ws_custom_dockerfile', 'custom.Dockerfile'
                ),
                '3.8',
                '',
                [],
            ),
        ),
    ],
)
def test_jinad_file_good(workdir, expected_response):
    d = DaemonFile(workdir=f'{cur_dir}/models/{workdir}')
    assert d.dockerfile.endswith(expected_response[0])
    assert d.python == expected_response[1]
    assert d.run == expected_response[2]
    assert d.ports == expected_response[3]


@pytest.mark.parametrize('workdir', ['bad_ws_wrong_dockerfile'])
def test_jinad_file_bad(workdir):
    with pytest.raises(DaemonInvalidDockerfile):
        DaemonFile(workdir=f'{cur_dir}/models/{workdir}')


def test_is_requirements_txt():
    for name in ['requirements.txt', 'custom-requirements.txt', 'requirements-gpu.txt']:
        assert is_requirements_txt(name)

    for name in ['blah.txt', 'a.py']:
        assert not is_requirements_txt(name)


def test_multiple_requirements_txt():
    assert sorted(
        DaemonFile(
            os.path.join(cur_dir, '../../distributed/test_dir_structures/src5')
        ).requirements.split()
    ) == ['sklearn', 'tinydb']
