import unittest

from jina.main.parser import set_pea_parser, set_pod_parser, set_gateway_parser
from jina.peapods.gateway import GatewayPea
from jina.peapods.pea import BasePea
from jina.peapods.pod import BasePod
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_pea_context(self):
        def _test_pea_context(runtime):
            args = set_pea_parser().parse_args(['--runtime', runtime])
            with BasePea(args):
                pass

            BasePea(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_pea_context(j)

    def test_pod_context(self):
        def _test_pod_context(runtime):
            args = set_pod_parser().parse_args(['--runtime', runtime])
            with BasePod(args):
                pass

            BasePod(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_pod_context(j)

    def test_gateway_pea(self):
        def _test_gateway_pea(runtime):
            args = set_gateway_parser().parse_args(['--runtime', runtime])
            with GatewayPea(args):
                pass

            GatewayPea(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_gateway_pea(j)


if __name__ == '__main__':
    unittest.main()
