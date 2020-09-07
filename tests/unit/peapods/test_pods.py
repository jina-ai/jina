from jina.main.parser import set_pod_parser, set_gateway_parser
from jina.peapods.pod import BasePod, GatewayPod, MutablePod, GatewayFlowPod, FlowPod


def test_pod_context(subtests):
    def _test_pod_context(runtime):
        args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])
        with BasePod(args):
            pass

        BasePod(args).start().close()

    for j in ('process', 'thread'):
        with subtests.test(runtime=j):
            _test_pod_context(j)


def test_gateway_pod(subtests):
    def _test_gateway_pod(runtime):
        args = set_gateway_parser().parse_args(['--runtime', runtime])
        with GatewayPod(args):
            pass

        GatewayPod(args).start().close()

    for j in ('process', 'thread'):
        with subtests.test(runtime=j):
            _test_gateway_pod(j)


def test_gatewayflow_pod(subtests):
    def _test_gateway_pod(runtime):
        with GatewayFlowPod({'runtime': runtime}):
            pass

        GatewayFlowPod({'runtime': runtime}).start().close()

    for j in ('process', 'thread'):
        with subtests.test(runtime=j):
            _test_gateway_pod(j)


def test_mutable_pod(subtests):
    def _test_mutable_pod(runtime):
        args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])

        with MutablePod(BasePod(args).peas_args):
            pass

        MutablePod(BasePod(args).peas_args).start().close()

    for j in ('process', 'thread'):
        with subtests.test(runtime=j):
            _test_mutable_pod(j)


def test_flow_pod(subtests):
    def _test_flow_pod(runtime):
        args = {'runtime': runtime, 'parallel': 2}
        with FlowPod(args):
            pass

        FlowPod(args).start().close()

    for j in ('process', 'thread'):
        with subtests.test(runtime=j):
            _test_flow_pod(j)


def test_pod_context_autoshutdown(subtests):
    def _test_pod_context(runtime):
        args = set_pod_parser().parse_args(['--runtime', runtime,
                                            '--parallel', '2',
                                            '--max-idle-time', '5',
                                            '--shutdown-idle'])
        with BasePod(args) as bp:
            bp.join()

        BasePod(args).start().close()

    for j in ('process', 'thread'):
        with subtests.test(runtime=j):
            _test_pod_context(j)


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


def test_pod_device_map():
    args = set_pod_parser().parse_args(['--name', 'pod',
                                        '--parallel', '4'])
    args.device_map = [1, 2]
    with BasePod(args):
        pass