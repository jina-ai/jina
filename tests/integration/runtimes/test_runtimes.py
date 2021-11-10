# test gateway, head and worker runtime by creating them manually in the most simple configuration
import multiprocessing
import time

import pytest

from jina import Document, Client
from jina.helper import random_port
from jina.parsers import set_gateway_parser, set_pea_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.peapods.runtimes.head import HeadRuntime
from jina.peapods.runtimes.worker import WorkerRuntime
from jina.types.message.common import ControlMessage


@pytest.mark.asyncio
async def test_runtimes_trivial_topology():
    worker_port = random_port()
    head_port = random_port()
    port_expose = random_port()
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
        args=(graph_description, pod_addresses, port_expose),
    )
    gateway_process.start()

    time.sleep(1.0)

    assert HeadRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{head_port}',
        shutdown_event=multiprocessing.Event(),
    )

    assert WorkerRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        shutdown_event=multiprocessing.Event(),
    )

    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlMessage(command='ACTIVATE')
    activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
    assert GrpcConnectionPool.send_message_sync(activate_msg, f'127.0.0.1:{head_port}')

    # send requests to the gateway
    async def async_inputs():
        for _ in range(20):
            yield Document(text='client0-Request')

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)
    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1

    # clean up runtimes
    gateway_process.terminate()
    head_process.terminate()
    worker_process.terminate()

    gateway_process.join()
    head_process.join()
    worker_process.join()

    assert gateway_process.exitcode == 0
    assert head_process.exitcode == 0
    assert worker_process.exitcode == 0


# test gateway, head and worker runtime by creating them manually in a more Flow like topology with branching
def test_runtimes_flow_topology():
    pass


# test something with shards

# test something with replicas

# test sth with uses_before/uses_after


def _create_worker_runtime(port):
    args = set_pea_parser().parse_args([])
    args.port_in = port
    # args.polling = PollingType.ALL
    # args.uses_before_address = 'fake_address'
    # args.uses_after_address = 'fake_address'
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_head_runtime(port):
    args = set_pea_parser().parse_args([])
    args.port_in = port
    # args.polling = PollingType.ALL
    # args.uses_before_address = 'fake_address'
    # args.uses_after_address = 'fake_address'

    connection_pool = GrpcConnectionPool()
    with HeadRuntime(args, connection_pool) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(graph_description, pod_addresses, port_expose):
    with GRPCGatewayRuntime(
        set_gateway_parser().parse_args(
            [
                '--grpc-data-requests',
                '--graph-description',
                graph_description,
                '--pods-addresses',
                pod_addresses,
                '--port-expose',
                str(port_expose),
            ]
        )
    ) as runtime:
        runtime.run_forever()
