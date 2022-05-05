import multiprocessing
import time

import pytest

from jina import Client, Document, helper
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.types.request.control import ControlRequest

from .test_runtimes import (
    _activate_runtimes,
    _create_gateway_runtime,
    _create_head_runtime,
    _create_worker_runtime,
    async_inputs,
)


def _create_worker(port):
    # create a single worker runtime
    p = multiprocessing.Process(target=_create_worker_runtime, args=(port,))
    p.start()
    time.sleep(0.1)
    return p


def _create_gateway(port, graph, pod_addr, protocol):
    # create a single worker runtime
    # create a single gateway runtime
    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph, pod_addr, port, protocol),
    )
    p.start()
    time.sleep(0.1)
    return p


def _create_head(port, polling):
    p = multiprocessing.Process(
        target=_create_head_runtime, args=(port, 'head', polling)
    )
    p.start()
    time.sleep(0.1)
    return p


def _send_request(gateway_port, protocol):
    """send request to gateway and see what happens"""
    c = Client(host='localhost', port=gateway_port, protocol=protocol)
    return c.post(
        '/', inputs=[Document(text='hi')], request_size=1, return_responses=True
    )


def _test_error(gateway_port, error_port, protocol):
    with pytest.raises(ConnectionError) as err_info:  # assert correct error is thrown
        _send_request(gateway_port, protocol)
    # assert error message contains useful info
    assert 'pod0' in err_info.value.args[0]
    assert str(error_port) in err_info.value.args[0]


@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
@pytest.mark.asyncio
async def test_runtimes_headless_topology(port_generator, protocol):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_port = port_generator()
    gateway_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    worker_process = _create_worker(worker_port)
    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, protocol
    )

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
    worker_process.join()

    try:
        # ----------- 1. test that useful errors are given -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, worker_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
        # ----------- 2. test that gateways remain alive -----------
        # just do the same again, expecting the same outcome
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, worker_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        worker_process.terminate()
        gateway_process.join()
        worker_process.join()


@pytest.mark.parametrize('terminate_head', [True, False])
@pytest.mark.parametrize('protocol', ['http', 'websocket', 'grpc'])
@pytest.mark.asyncio
async def test_runtimes_headful_topology(port_generator, protocol, terminate_head):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_port = port_generator()
    gateway_port = port_generator()
    head_port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    head_process = _create_head(head_port, 'ANY')
    worker_process = _create_worker(worker_port)
    gateway_process = _create_gateway(
        gateway_port, graph_description, pod_addresses, protocol
    )

    time.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{head_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

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

    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
    GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    # terminate pod, either head or worker behind the head
    if terminate_head:
        head_process.terminate()
        head_process.join()
        error_port = head_port
    else:
        worker_process.terminate()  # kill worker
        worker_process.join()
        error_port = worker_port

    try:
        # ----------- 1. test that useful errors are given -----------
        # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, error_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
        # ----------- 2. test that gateways remain alive -----------
        # just do the same again, expecting the same outcome
        p = multiprocessing.Process(
            target=_test_error, args=(gateway_port, error_port, protocol)
        )
        p.start()
        p.join()
        assert (
            p.exitcode == 0
        )  # if exitcode != 0 then test in other process did not pass and this should fail
    except Exception:
        raise
    finally:  # clean up runtimes
        gateway_process.terminate()
        worker_process.terminate()
        head_process.terminate()
        gateway_process.join()
        worker_process.join()
        head_process.join()
