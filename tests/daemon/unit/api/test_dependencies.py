import os
from shutil import copy
from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from jina.flow.base import Flow
from jina.enums import GatewayProtocolType
from daemon.api import dependencies
from daemon.helper import change_cwd
from daemon.models.id import DaemonID
from daemon.api.dependencies import FlowDepends, Environment


cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_flow_depends_localpath(monkeypatch, tmpdir):
    filename = os.path.join(cur_dir, 'flow1.yml')
    monkeypatch.setattr(dependencies, 'change_cwd', nullcontext)
    monkeypatch.setattr(dependencies, 'get_workspace_path', lambda *args: filename)
    monkeypatch.setattr(FlowDepends, 'newfile', os.path.join(tmpdir, 'abc.yml'))
    f = FlowDepends(DaemonID('jworkspace'), filename, Environment(envs=['a=b']))
    assert str(f.localpath()) == filename

    with pytest.raises(HTTPException) as e:
        monkeypatch.setattr(dependencies, "get_workspace_path", lambda *args: 'abc')
        f = FlowDepends(DaemonID('jworkspace'), filename, Environment(envs=['a=b']))
        f.localpath()


def test_flow_depends_load_and_dump(monkeypatch, tmpdir):
    filename = os.path.join(cur_dir, 'flow2.yml')
    monkeypatch.setattr(dependencies, 'get_workspace_path', lambda *args: tmpdir)
    monkeypatch.setattr(
        FlowDepends, 'localpath', lambda *args: os.path.join(tmpdir, filename)
    )
    monkeypatch.setattr(FlowDepends, 'newfile', os.path.join(tmpdir, 'abc.yml'))
    monkeypatch.setattr(FlowDepends, 'newname', 'abc.yml')
    copy(os.path.join(cur_dir, filename), tmpdir)

    fd = FlowDepends(
        workspace_id=DaemonID('jworkspace'),
        filename=filename,
        envs=Environment(envs=['a=b']),
    )
    with change_cwd(tmpdir):
        f: Flow = Flow.load_config(fd.params.uses).build()
        assert f.port_expose == 12345
        assert f.protocol == GatewayProtocolType.HTTP
        assert f['gateway'].args.runs_in_docker
        assert f['local_replicas'].args.runs_in_docker
        assert f['local_replicas'].args.port_in == 45678
        assert f['local_replicas'].args.port_in is not None
        assert all(
            port in fd.ports.ports
            for port in [
                f.port_expose,
                f['gateway'].args.port_in,
                f['gateway'].args.port_out,
                f['gateway'].args.port_ctrl,
                f['local_replicas'].args.port_in,
                f['local_replicas'].args.port_out,
                f['local_replicas'].args.port_ctrl,
                f['local_compound'].head_args.port_in,
                f['local_compound'].tail_args.port_out,
            ]
        )


def test_dump_grpc_data_requests(monkeypatch, tmpdir):
    filename = os.path.join(cur_dir, 'flow3.yml')
    monkeypatch.setattr(dependencies, 'get_workspace_path', lambda *args: tmpdir)
    monkeypatch.setattr(
        FlowDepends, 'localpath', lambda *args: os.path.join(tmpdir, filename)
    )
    monkeypatch.setattr(FlowDepends, 'newname', os.path.join(tmpdir, 'abc.yml'))
    monkeypatch.setattr(FlowDepends, 'newfile', 'abc.yml')
    copy(os.path.join(cur_dir, filename), tmpdir)

    fd = FlowDepends(
        workspace_id=DaemonID('jworkspace'),
        filename=filename,
        envs=Environment(envs=['a=b']),
    )
    with change_cwd(tmpdir):
        f: Flow = Flow.load_config(fd.params.uses).build()
        assert f.port_expose == 12345
        assert f.protocol == GatewayProtocolType.HTTP
        assert f['gateway'].args.runs_in_docker
        assert f['local_replicas'].args.runs_in_docker
        assert f['local_replicas'].args.port_in == 45678
        assert f.gateway_args.grpc_data_requests


@pytest.mark.parametrize(
    ('envs, expected'),
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
def test_environment(envs, expected):
    assert Environment(envs=envs).vars == expected
