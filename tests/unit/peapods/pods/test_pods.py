import os

import pytest
from jina.executors import BaseExecutor
from jina.parser import set_pod_parser, set_gateway_parser
from jina.peapods import Pod
from jina.peapods.pods import BasePod
from jina.peapods.pods.flow import FlowPod
from jina.peapods.pods.gateway import GatewayFlowPod, GatewayPod
#from jina.peapods.pods.mutable import MutablePod


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


# @pytest.mark.parametrize('runtime', ['process', 'thread'])
# def test_mutable_pod(runtime):
#     args = set_pod_parser().parse_args(['--runtime', runtime, '--parallel', '2'])
#
#     with MutablePod(BasePod(args).peas_args):
#         pass
#
#     MutablePod(BasePod(args).peas_args).start().close()


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


def test_pod_env_setting():
    class EnvChecker(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # pea/pod-specific
            assert os.environ['key1'] == 'value1'
            assert os.environ['key2'] == 'value2'
            # inherit from parent process
            assert os.environ['key_parent'] == 'value3'

    os.environ['key_parent'] = 'value3'

    with Pod(uses='EnvChecker', env=['key1=value1', 'key2=value2']):
        pass

    # should not affect the main process
    assert 'key1' not in os.environ
    assert 'key2' not in os.environ
    assert 'key_parent' in os.environ

    os.unsetenv('key_parent')


def test_pod_env_setting_thread():
    class EnvChecker(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # pea/pod-specific
            assert 'key1' not in os.environ
            assert 'key2' not in os.environ
            # inherit from parent process
            assert os.environ['key_parent'] == 'value3'

    os.environ['key_parent'] = 'value3'

    with Pod(uses='EnvChecker', env=['key1=value1', 'key2=value2'], runtime='thread'):
        pass

    # should not affect the main process
    assert 'key1' not in os.environ
    assert 'key2' not in os.environ
    assert 'key_parent' in os.environ

    os.unsetenv('key_parent')
