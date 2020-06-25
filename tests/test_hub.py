import os
import unittest

from jina.hubapi.docker import HubIO
from jina.main.parser import set_hub_build_parser, set_hub_pushpull_parser
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    @unittest.skipIf('GITHUB_WORKFLOW' in os.environ, 'skip the stdin test on github workflow')
    def test_hub_build_pull(self):
        args = set_hub_build_parser().parse_args(['./hub-mwu', '--pull', '--push'])
        HubIO(args).build()

        args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder'])
        HubIO(args).pull()

        args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
        HubIO(args).pull()
