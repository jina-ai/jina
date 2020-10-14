import pytest

from jina.parser import set_pod_parser, set_gateway_parser
from jina.peapods.pod import BasePod, GatewayPod, MutablePod, GatewayFlowPod, FlowPod


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_context(runtime):
    args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])
    with BasePod(args):
        pass

    BasePod(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_gateway_pod(runtime):
    args = set_gateway_parser().parse_args(['--runtime', runtime])
    with GatewayPod(args):
        pass

    GatewayPod(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_gateway_pod(runtime):
    with GatewayFlowPod({'runtime': runtime}):
        pass

    GatewayFlowPod({'runtime': runtime}).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_mutable_pod(runtime):
    args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])

    with MutablePod(BasePod(args).peas_args):
        pass

    MutablePod(BasePod(args).peas_args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_flow_pod(runtime):
    args = {'runtime': runtime, 'parallel': 2}
    with FlowPod(args):
        pass

    FlowPod(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_context(runtime):
    args = set_pod_parser().parse_args(['--runtime', runtime,
                                        '--parallel', '2',
                                        '--max-idle-time', '5',
                                        '--shutdown-idle'])
    with BasePod(args) as bp:
        bp.join()

    BasePod(args).start().close()


def test_pod_gracefully_close_idle():
    import time
    args = set_pod_parser().parse_args(['--name', 'pod',
                                        '--parallel', '2',
                                        '--max-idle-time', '4',
                                        '--shutdown-idle'])

    start_time = time.time()
    with BasePod(args) as bp:
        while not bp.is_shutdown:
            time.sleep(1.5)

    end_time = time.time()
    elapsed_time = end_time - start_time
    assert elapsed_time > 4
