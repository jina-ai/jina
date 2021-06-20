import os

import pytest

from fastapi import HTTPException
from daemon.api import dependencies
from daemon.models.id import DaemonID
from daemon.api.dependencies import FlowDepends


cur_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(cur_dir, 'flow1.yml')


def test_flow_depends_localpath(monkeypatch):
    monkeypatch.setattr(dependencies, "get_workspace_path", lambda *args: filename)
    f = FlowDepends(DaemonID('jworkspace'), filename)
    assert str(f.localpath()) == filename

    with pytest.raises(HTTPException) as e:
        monkeypatch.setattr(dependencies, "get_workspace_path", lambda *args: 'abc')
        f = FlowDepends(DaemonID('jworkspace'), filename)
        f.localpath()


def test_flow_depends_ports():
    expected_port = 28956
    f = FlowDepends(DaemonID('jworkspace'), filename)
    assert f.port_expose == expected_port
    assert f.ports == {f'{expected_port}/tcp': expected_port}
