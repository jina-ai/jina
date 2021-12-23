from jina.peapods.peas.factory import PeaFactory

from jina.hubble.hubio import HubIO
from jina.parsers import set_pea_parser


def test_container_pea(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_pull(self):
        return 'docker://jinahub/dummy_executor'

    monkeypatch.setattr(HubIO, 'pull', _mock_pull)

    args = set_pea_parser().parse_args(['--uses', 'jinahub+docker://DummyExecutor'])
    pea = PeaFactory.build_pea(args)
    assert pea.args.uses == 'docker://jinahub/dummy_executor'
    assert pea.name == 'ContainerPea'
