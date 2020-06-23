from jina.hubapi.docker import DockerIO
from jina.main.parser import set_hub_build_parser, set_hub_pushpull_parser
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_hub_build_pull(self):
        args = set_hub_build_parser().parse_args(['./hub-mwu', '--pull', '--push'])
        DockerIO(args).build()

        args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder'])
        DockerIO(args).pull()

        args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
        DockerIO(args).pull()
