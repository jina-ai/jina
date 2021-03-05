import pytest

from jina.enums import RemoteAccessType
from jina.flow import Flow
from jina.parsers import set_pea_parser, set_pod_parser
from jina.peapods.pods import BasePod
from jina.peapods.runtimes.ssh import SSHRuntime
from jina.proto import jina_pb2


@pytest.mark.skip(
    'works locally, but until I findout how to mock ssh, this has to be skipped'
)
def test_ssh_pea():
    p = set_pea_parser().parse_args(['--host', 'pi@172.16.1.110', '--timeout', '5000'])

    with SSHRuntime(p) as pp:
        assert pp.status.envelope.status.code == jina_pb2.StatusProto.READY

    assert pp.status is None


@pytest.mark.skip(
    'works locally, but until I find out how to mock ssh, this has to be skipped'
)
def test_ssh_pod():
    p = set_pod_parser().parse_args(['--host', 'pi@172.16.1.110', '--timeout', '5000'])
    with SSHRuntime(p) as pp:
        assert pp.status.envelope.status.code == jina_pb2.StatusProto.READY

    assert pp.status is None


@pytest.mark.skip('not implemented yet')
def test_ssh_mutable_pod():
    p = set_pod_parser().parse_args(['--host', 'pi@172.16.1.110', '--timeout', '5000'])
    p = BasePod(p)
    with SSHRuntime(p) as pp:
        assert pp.status.envelope.status.code == jina_pb2.StatusProto.READY

    assert pp.status is None


@pytest.mark.skip('not implemented yet')
def test_flow():
    f = Flow().add().add(host='pi@172.16.1.110', remote_manager=RemoteAccessType.SSH)
    with f:
        pass
