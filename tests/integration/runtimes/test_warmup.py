import threading
import time

import pytest

from jina import Executor, Flow

SLOW_EXECUTOR_SLEEP_TIME = 3


class SlowExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        time.sleep(SLOW_EXECUTOR_SLEEP_TIME)


@pytest.fixture
def stop_event():
    return threading.Event()


def flow_run(flow, stop_event):
    with flow:
        flow.block(stop_event)


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
async def test_gateway_warmup_fast_executor(protocol, capfd):
    flow = Flow(protocol=protocol).add()

    with flow:
        time.sleep(1)
        out, _ = capfd.readouterr()
        assert 'got an endpoint discovery request' in out


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('early_teardown', [False, True])
async def test_gateway_warmup_slow_executor(
    protocol, capfd, stop_event, early_teardown
):
    flow = Flow(protocol=protocol).add(name='slowExecutor', uses='SlowExecutor')
    t = threading.Thread(target=flow_run, args=(flow, stop_event))
    t.start()

    try:
        if early_teardown:
            time.sleep(1)
            stop_event.set()
            out, _ = capfd.readouterr()
            assert not 'got an endpoint discovery request' in out
        else:
            # requires high sleep time to account for Flow readiness and properly capture the output logs
            time.sleep(SLOW_EXECUTOR_SLEEP_TIME * 3)
            out, _ = capfd.readouterr()
            assert 'got an endpoint discovery request' in out
    finally:
        if not stop_event.is_set():
            stop_event.set()
        t.join()


@pytest.mark.asyncio
async def test_multi_protocol_gateway_warmup_fast_executor(port_generator, capfd):
    http_port = port_generator()
    grpc_port = port_generator()
    websocket_port = port_generator()
    flow = (
        Flow()
        .config_gateway(
            port=[http_port, grpc_port, websocket_port],
            protocol=['http', 'grpc', 'websocket'],
        )
        .add()
    )

    with flow:
        time.sleep(1)
        out, _ = capfd.readouterr()
        assert 'got an endpoint discovery request' in out


@pytest.mark.asyncio
@pytest.mark.parametrize('early_teardown', [False, True])
async def test_multi_protocol_gateway_warmup_slow_executor(
    port_generator, capfd, early_teardown, stop_event
):
    http_port = port_generator()
    grpc_port = port_generator()
    websocket_port = port_generator()
    flow = (
        Flow()
        .config_gateway(
            port=[http_port, grpc_port, websocket_port],
            protocol=['http', 'grpc', 'websocket'],
        )
        .add(name='slowExecutor', uses='SlowExecutor')
    )
    t = threading.Thread(target=flow_run, args=(flow, stop_event))
    t.start()

    try:
        if early_teardown:
            time.sleep(1)
            stop_event.set()
            out, _ = capfd.readouterr()
            assert not 'got an endpoint discovery request' in out
        else:
            # requires high sleep time to account for Flow readiness and properly capture the output logs
            time.sleep(SLOW_EXECUTOR_SLEEP_TIME * 3)
            out, _ = capfd.readouterr()
            assert 'got an endpoint discovery request' in out
    finally:
        if not stop_event.is_set():
            stop_event.set()
        t.join()
