from hubble.executor.hubio import HubIO

from jina.orchestrate.pods.factory import PodFactory
from jina.parsers import set_pod_parser


def test_container_pod(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_pull(self):
        return 'docker://jinahub/dummy_executor'

    monkeypatch.setattr(HubIO, 'pull', _mock_pull)

    args = set_pod_parser().parse_args(['--uses', 'jinahub+docker://DummyExecutor'])
    pod = PodFactory.build_pod(args)
    assert pod.args.uses == 'docker://jinahub/dummy_executor'
    assert pod.name == 'ContainerPod'
