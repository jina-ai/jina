import unittest

from jina.main.parser import set_pea_parser, set_pod_parser, set_gateway_parser
from jina.peapods.gateway import GatewayPea
from jina.peapods.pea import BasePea
from jina.peapods.pod import BasePod, GatewayPod, MutablePod, GatewayFlowPod, FlowPod
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

    def test_address_in_use(self):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        with BasePea(args1), BasePea(args2):
            pass

        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        with BasePea(args1), BasePea(args2):
            pass

        print('everything should quit gracefully')

    def test_pod_context(self):
        def _test_pod_context(runtime):
            args = set_pod_parser().parse_args(['--runtime', runtime, '--replicas', '2'])
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

    def test_gateway_pod(self):
        def _test_gateway_pod(runtime):
            args = set_gateway_parser().parse_args(['--runtime', runtime])
            with GatewayPod(args):
                pass

            GatewayPod(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_gateway_pod(j)

    def test_gatewayflow_pod(self):
        def _test_gateway_pod(runtime):
            with GatewayFlowPod({'runtime': runtime}):
                pass

            GatewayFlowPod({'runtime': runtime}).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_gateway_pod(j)

    def test_mutable_pod(self):
        def _test_mutable_pod(runtime):
            args = set_pod_parser().parse_args(['--runtime', runtime, '--replicas', '2'])

            with MutablePod(BasePod(args).peas_args):
                pass

            MutablePod(BasePod(args).peas_args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_mutable_pod(j)

    def test_flow_pod(self):
        def _test_flow_pod(runtime):
            args = {'runtime': runtime, 'replicas': 2}
            with FlowPod(args):
                pass

            FlowPod(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_flow_pod(j)

    def test_pod_context_autoshutdown(self):
        def _test_pod_context(runtime):
            args = set_pod_parser().parse_args(['--runtime', runtime,
                                                '--replicas', '2',
                                                '--max-idle-time', '5',
                                                '--shutdown-idle'])
            with BasePod(args) as bp:
                bp.join()

            BasePod(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_pod_context(j)


if __name__ == '__main__':
    unittest.main()
