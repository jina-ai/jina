import multiprocessing

import pytest

from jina import Client
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import _generate_args


def _create_worker_runtime(port, name='', executor=None):
    args = _generate_args()
    args.port = port
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(graph_description, pod_addresses, port, protocol='grpc'):
    with GatewayRuntime(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
                '--protocol',
                protocol,
            ]
        )
    ) as runtime:
        runtime.run_forever()


def _setup(worker_port, port, protocol):
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
    return worker_process, gateway_process


@pytest.mark.parametrize('protocol', ['http'])
def test_dry_run_of_flow(port_generator, protocol):
    worker_port = port_generator()
    port = port_generator()
    worker_process, gateway_process = _setup(worker_port, port, protocol)
    # send requests to the gateway
    c = Client(host='localhost', port=port, protocol=protocol)
    dry_run_alive = c.is_flow_ready()

    # _teardown(worker_process, gateway_process, dry_run_alive)
    worker_process.terminate()
    worker_process.join()

    dry_run_worker_removed = c.is_flow_ready()

    gateway_process.terminate()
    gateway_process.join()

    assert dry_run_alive
    assert not dry_run_worker_removed

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
async def test_async_dry_run_of_flow(port_generator, protocol):
    worker_port = port_generator()
    port = port_generator()
    worker_process, gateway_process = _setup(worker_port, port, protocol)
    # send requests to the gateway
    c = Client(host='localhost', asyncio=True, port=port, protocol=protocol)
    dry_run_alive = await c.is_flow_ready()

    # _teardown(worker_process, gateway_process, dry_run_alive)
    worker_process.terminate()
    worker_process.join()

    dry_run_worker_removed = await c.is_flow_ready()

    gateway_process.terminate()
    gateway_process.join()

    assert dry_run_alive
    assert not dry_run_worker_removed

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0
