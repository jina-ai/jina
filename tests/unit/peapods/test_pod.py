import unittest

from jina.main.parser import set_pod_parser, set_gateway_parser
from jina.peapods.pod import BasePod, GatewayPod, MutablePod, GatewayFlowPod, FlowPod
from tests import JinaTestCase


class PodTestCase(JinaTestCase):

    def test_pod_context(self):
        def _test_pod_context(runtime):
            args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])
            with BasePod(args):
                pass

            BasePod(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_pod_context(j)

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
            args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])

            with MutablePod(BasePod(args).peas_args):
                pass

            MutablePod(BasePod(args).peas_args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_mutable_pod(j)

    def test_flow_pod(self):
        def _test_flow_pod(runtime):
            args = {'runtime': runtime, 'parallel': 2}
            with FlowPod(args):
                pass

            FlowPod(args).start().close()

        for j in ('process', 'thread'):
            with self.subTest(runtime=j):
                _test_flow_pod(j)

    def test_pod_context_autoshutdown(self):
        def _test_pod_context(runtime):
            args = set_pod_parser().parse_args(['--runtime', runtime,
                                                '--parallel', '2',
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
