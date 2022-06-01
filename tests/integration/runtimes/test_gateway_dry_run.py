import asyncio
import json
import multiprocessing
import threading
import time
from collections import defaultdict

import pytest

from jina import Client, Document, Executor, requests
from jina.enums import PollingType
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.serve.runtimes.gateway.http import HTTPGatewayRuntime
from jina.serve.runtimes.gateway.websocket import WebSocketGatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime


def _create_worker_runtime(port, name='', executor=None):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(graph_description, pod_addresses, port, protocol='grpc'):
    if protocol == 'http':
        gateway_runtime = HTTPGatewayRuntime
    elif protocol == 'websocket':
        gateway_runtime = WebSocketGatewayRuntime
    else:
        gateway_runtime = GRPCGatewayRuntime
    with gateway_runtime(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
            ]
        )
    ) as runtime:
        runtime.run_forever()


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_dry_run_of_flow(port_generator, protocol):
    worker_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    # create a single worker runtime
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port,)
    )
    worker_process.start()

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port, protocol),
    )
    gateway_process.start()

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

    # send requests to the gateway
    c = Client(host='localhost', port=port, asyncio=True, protocol=protocol)
    dry_run_alive = c.dry_run()

    worker_process.terminate()
    worker_process.join()

    dry_run_worker_removed = c.dry_run()

    gateway_process.terminate()
    gateway_process.join()

    assert dry_run_alive
    assert not dry_run_worker_removed

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0
