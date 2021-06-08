import os
from daemon.models.id import DaemonID
from daemon.api import dependencies
from daemon.api.dependencies import FlowDepends

import pytest

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    'filename, expected',
    [
        ('flow1.yml', 28956),
        ('flow2.yml', 34567)
    ]
)
def test_flow_depends_ports(filename, expected, monkeypatch):
    monkeypatch.setattr(dependencies, 'random_port', lambda: expected)
    monkeypatch.setattr(FlowDepends, 'validate', lambda *args: os.path.join(cur_dir, filename))
    f = FlowDepends(DaemonID('jworkspace'), filename)
    assert f.port_expose == expected
    assert f.ports == {f'{expected}/tcp': expected}
