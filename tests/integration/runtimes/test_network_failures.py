import asyncio
import json
import multiprocessing
import threading
import time

import grpc.aio
import pytest

from jina import Client, Document, Executor, requests
from jina.enums import PollingType
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.serve.runtimes.head import HeadRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from jina.types.request.control import ControlRequest

from .test_runtimes import (
    _activate_runtimes,
    _create_gateway_runtime,
    _create_head_runtime,
    _create_worker_runtime,
    async_inputs,
)


@pytest.mark.asyncio
# create gateway, head and workers manually, then terminate head process to provoke an error
# TODO(johannes) actually make this one fail
async def test_runtimes_head_topology(port_generator):
    worker_port = port_generator()
    head_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single worker runtime
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port,)
    )
    worker_process.start()

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port,)
    )
    head_process.start()

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

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
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
    GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    # send requests to the gateway
    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    head_process.terminate()
    worker_process.terminate()

    gateway_process.join()
    head_process.join()
    worker_process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1

    assert gateway_process.exitcode == 0
    assert head_process.exitcode == 0
    assert worker_process.exitcode == 0


# create gateway and workers manually, then terminate worker process to provoke an error
# TODO(johannes) meaningful asserts
# TODO(johannes) have different workers and parametrize their failure. Assert correct worker is identified in error message
def test_runtimes_headless_topology(port_generator):
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
        args=(graph_description, pod_addresses, gateway_port),
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

    worker_process.terminate()
    # send requests to the gateway
    try:
        c = Client(host='localhost', port=gateway_port)
        responses = c.post(
            '/', inputs=async_inputs, request_size=1, return_responses=True
        )
        response_list = []
        for response in responses:
            response_list.append(response)
    except Exception:
        gateway_process.terminate()
        worker_process.terminate()
        raise

    # clean up runtimes
    gateway_process.terminate()
    worker_process.terminate()

    gateway_process.join()
    worker_process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0
