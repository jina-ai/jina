import os
from contextlib import nullcontext

import pytest

from fastapi import HTTPException
from daemon.api import dependencies
from daemon.models.id import DaemonID
from daemon.api.dependencies import FlowDepends, Environment


cur_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(cur_dir, 'flow1.yml')


def test_flow_depends_localpath(monkeypatch):
    monkeypatch.setattr(dependencies, 'change_cwd', nullcontext)
    monkeypatch.setattr(dependencies, 'get_workspace_path', lambda *args: filename)
    f = FlowDepends(DaemonID('jworkspace'), filename, Environment(envs=['a=b']))
    assert str(f.localpath()) == filename

    with pytest.raises(HTTPException) as e:
        monkeypatch.setattr(dependencies, "get_workspace_path", lambda *args: 'abc')
        f = FlowDepends(DaemonID('jworkspace'), filename, Environment(envs=['a=b']))
        f.localpath()


def test_flow_depends_ports(monkeypatch):
    expected_port = 28956
    monkeypatch.setattr(dependencies, 'change_cwd', nullcontext)
    monkeypatch.setattr(dependencies, 'get_workspace_path', lambda *args: filename)
    f = FlowDepends(DaemonID('jworkspace'), filename, Environment(envs=['a=b']))
    assert f.port_expose == expected_port
    assert f.ports == {f'{expected_port}/tcp': expected_port}


@pytest.mark.parametrize(
    ('args, expected'),
    [
        (['a=b'], {'a': 'b'}),
        (
            ['PORT_EXPOSE=12345', 'password=*dU-rTAv3 u'],
            {'PORT_EXPOSE': '12345', 'password': '*dU-rTAv3 u'},
        ),
        (['a=\nbd'], {'a': 'bd'}),
        (['a:b'], {}),
    ],
)
def test_environment(args, expected):
    assert Environment(envs=args).vars == expected
