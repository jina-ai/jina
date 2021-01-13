import os

from jina import Flow
from jina.docker.hubio import HubIO
from jina.parsers.hub import set_hub_build_parser
from jina import __version__ as jina_version

from .dummyhub import DummyHubExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_hubio_build():
    drivers = DummyHubExecutor.default_drivers();
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'dummyhub'), '--timeout-ready', '20000', '--test-uses', '--raise-error'])
    HubIO(args).build()
    with Flow().add(uses=f'docker://jinahub/pod.crafter.dummyhubexecutor:0.0.0-{jina_version}',
                    timeout_ready=20000):
        pass