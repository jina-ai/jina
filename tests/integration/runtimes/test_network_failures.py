import asyncio
import multiprocessing
import time

import pytest

from jina import Client, Document
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.types.request.control import ControlRequest

from .test_runtimes import (
    _create_gateway_runtime,
    _create_head_runtime,
    _create_worker_runtime,
    async_inputs,
)


@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
def test_runtimes_headless_topology(port_generator, protocol):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_port = port_generator()
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    # create a single worker runtime
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port,)
    )
    worker_process.start()

    time.sleep(0.1)

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, gateway_port, protocol),
    )
    gateway_process.start()

    time.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    worker_process.terminate()  # kill worker

    def _send_request_test_error():
        """send request to gateway and see what happens"""
        with pytest.raises(ConnectionError) as err_info:
            c = Client(host='localhost', port=gateway_port, protocol=protocol)
            responses = c.post(
                '/', inputs=[Document(text='hi')], request_size=1, return_responses=True
            )
        # assert error message contains useful info
        assert 'pod0' in err_info.value.args[0]
        assert str(worker_port) in err_info.value.args[0]

    try:
        # ----------- 1. test that useful errors are given -----------
        _send_request_test_error()
        # ----------- 2. test that gateways remain alive -----------
        _send_request_test_error()  # just repeat the test, expecting the same result
    finally:  # clean up runtimes
        gateway_process.terminate()
        worker_process.terminate()
        gateway_process.join()
        worker_process.join()
