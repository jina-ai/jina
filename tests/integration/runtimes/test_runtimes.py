import asyncio
import json
import multiprocessing
import threading
import time

import pytest

from jina import Document, Executor, Client, requests
from jina.enums import PollingType
from jina.parsers import set_gateway_parser, set_pea_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.runtimes.asyncio import AsyncNewLoopRuntime
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.peapods.runtimes.head import HeadRuntime
from jina.peapods.runtimes.worker import WorkerRuntime
from jina.types.request.control import ControlRequest


@pytest.mark.asyncio
# test gateway, head and worker runtime by creating them manually in the most simple configuration
async def test_runtimes_trivial_topology(port_generator):
    worker_port = port_generator()
    head_port = port_generator()
    port_expose = port_generator()
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
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity('worker', '127.0.0.1', worker_port)
    GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')

    # send requests to the gateway
    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
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


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['end-gateway'],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'merger': ['pod_last'],
        'pod5': ['merger'],
        'pod3': ['merger'],
        'pod6': [],  # hanging_pod
        'pod_last': ['end-gateway'],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize('uses_before', [True, False])
@pytest.mark.parametrize('uses_after', [True, False])
# test gateway, head and worker runtime by creating them manually in a more Flow like topology with branching/merging
async def test_runtimes_flow_topology(
    complete_graph_dict, uses_before, uses_after, port_generator
):
    pods = [
        pod_name for pod_name in complete_graph_dict.keys() if 'gateway' not in pod_name
    ]
    runtime_processes = []
    pod_addresses = '{'
    for pod in pods:
        if uses_before:
            uses_before_port, uses_before_process = await _create_worker(
                pod, port_generator, type='uses_before'
            )
            AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
                timeout=5.0,
                ready_or_shutdown_event=threading.Event(),
                ctrl_address=f'127.0.0.1:{uses_before_port}',
            )
            runtime_processes.append(uses_before_process)
        if uses_after:
            uses_after_port, uses_after_process = await _create_worker(
                pod, port_generator, type='uses_after'
            )
            AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
                timeout=5.0,
                ready_or_shutdown_event=threading.Event(),
                ctrl_address=f'127.0.0.1:{uses_after_port}',
            )
            runtime_processes.append(uses_after_process)

        # create head
        head_port = port_generator()
        pod_addresses += f'"{pod}": ["0.0.0.0:{head_port}"],'
        head_process = multiprocessing.Process(
            target=_create_head_runtime,
            args=(
                head_port,
                f'{pod}/head',
                'ANY',
                f'127.0.0.1:{uses_before_port}' if uses_before else None,
                f'127.0.0.1:{uses_after_port}' if uses_after else None,
            ),
        )
        runtime_processes.append(head_process)
        head_process.start()

        # create worker
        worker_port, worker_process = await _create_worker(pod, port_generator)
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ready_or_shutdown_event=threading.Event(),
            ctrl_address=f'127.0.0.1:{worker_port}',
        )
        runtime_processes.append(worker_process)
        await asyncio.sleep(0.1)

        await _activate_worker(head_port, worker_port)

    # remove last comma
    pod_addresses = pod_addresses[:-1]
    pod_addresses += '}'
    port_expose = port_generator()

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(json.dumps(complete_graph_dict), pod_addresses, port_expose),
    )
    gateway_process.start()

    await asyncio.sleep(0.1)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    # send requests to the gateway
    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    for process in runtime_processes:
        process.terminate()

    gateway_process.join()
    for process in runtime_processes:
        process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1

    assert gateway_process.exitcode == 0
    for process in runtime_processes:
        assert process.exitcode == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('polling', ['ALL', 'ANY'])
# test simple topology with shards
async def test_runtimes_shards(polling, port_generator):
    head_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port, 'head', polling)
    )
    head_process.start()

    # create the shards
    shard_processes = []
    worker_ports = []
    for i in range(10):
        # create worker
        worker_port = port_generator()
        # create a single worker runtime
        worker_process = multiprocessing.Process(
            target=_create_worker_runtime, args=(worker_port, f'pod0/shard/{i}')
        )
        shard_processes.append(worker_process)
        worker_process.start()

        await asyncio.sleep(0.1)
        worker_ports.append(worker_port)

    await _activate_runtimes(head_port, worker_ports)

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port_expose),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    head_process.terminate()
    for shard_process in shard_processes:
        shard_process.terminate()

    gateway_process.join()
    head_process.join()
    for shard_process in shard_processes:
        shard_process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1 if polling == 'ANY' else len(shard_processes)

    assert gateway_process.exitcode == 0
    assert head_process.exitcode == 0
    for shard_process in shard_processes:
        assert shard_process.exitcode == 0


@pytest.mark.asyncio
# test simple topology with replicas
async def test_runtimes_replicas(port_generator):
    head_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port, 'head')
    )
    head_process.start()

    # create the shards
    replica_processes = []
    worker_ports = []
    for i in range(10):
        # create worker
        worker_port = port_generator()
        # create a single worker runtime
        worker_process = multiprocessing.Process(
            target=_create_worker_runtime, args=(worker_port, f'pod0/{i}')
        )
        replica_processes.append(worker_process)
        worker_process.start()

        await asyncio.sleep(0.1)
        worker_ports.append(worker_port)

    await _activate_runtimes(head_port, worker_ports)

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port_expose),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    head_process.terminate()
    for replica_process in replica_processes:
        replica_process.terminate()

    gateway_process.join()
    head_process.join()
    for replica_process in replica_processes:
        replica_process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1

    assert gateway_process.exitcode == 0
    assert head_process.exitcode == 0
    for replica_process in replica_processes:
        assert replica_process.exitcode == 0


@pytest.mark.asyncio
async def test_runtimes_with_executor(port_generator):
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    runtime_processes = []

    uses_before_port, uses_before_process = await _create_worker(
        'pod0', port_generator, type='uses_before', executor='NameChangeExecutor'
    )
    runtime_processes.append(uses_before_process)

    uses_after_port, uses_after_process = await _create_worker(
        'pod0', port_generator, type='uses_after', executor='NameChangeExecutor'
    )
    runtime_processes.append(uses_after_process)

    # create head
    head_port = port_generator()
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'
    head_process = multiprocessing.Process(
        target=_create_head_runtime,
        args=(
            head_port,
            f'pod0/head',
            'ALL',
            f'127.0.0.1:{uses_before_port}',
            f'127.0.0.1:{uses_after_port}',
        ),
    )
    runtime_processes.append(head_process)
    head_process.start()
    runtime_processes.append(head_process)

    # create some shards
    worker_ports = []
    for i in range(10):
        # create worker
        worker_port, worker_process = await _create_worker(
            'pod0', port_generator, type=f'shards/{i}', executor='NameChangeExecutor'
        )
        runtime_processes.append(worker_process)
        await asyncio.sleep(0.1)
        worker_ports.append(worker_port)

    await _activate_runtimes(head_port, worker_ports)

    # create a single gateway runtime
    port_expose = port_generator()
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port_expose),
    )
    gateway_process.start()
    runtime_processes.append(gateway_process)

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response.docs)

    # clean up runtimes
    for process in runtime_processes:
        process.terminate()

    for process in runtime_processes:
        process.join()

    assert len(response_list) == 20
    assert (
        len(response_list[0]) == (1 + 1 + 1) * 10 + 1
    )  # 1 starting doc + 1 uses_before + every exec adds 1 * 10 shards + 1 doc uses_after

    doc_texts = [doc.text for doc in response_list[0]]
    assert doc_texts.count('client0-Request') == 10
    assert doc_texts.count('pod0/uses_before') == 10
    assert doc_texts.count('pod0/uses_after') == 1
    for i in range(10):
        assert doc_texts.count(f'pod0/shards/{i}') == 1

    for process in runtime_processes:
        assert process.exitcode == 0


@pytest.mark.asyncio
async def test_runtimes_gateway_worker_direct_connection(port_generator):
    worker_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    # create the shards
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port, f'pod0')
    )
    worker_process.start()

    await asyncio.sleep(0.1)
    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port_expose),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port_expose, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    worker_process.terminate()
    gateway_process.join()
    worker_process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1
    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0


@pytest.mark.asyncio
async def test_runtimes_with_replicas_advance_faster(port_generator):
    head_port = port_generator()
    port_expose = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port, 'head')
    )
    head_process.start()

    # create the shards
    replica_processes = []
    worker_ports = []
    for i in range(10):
        # create worker
        worker_port = port_generator()
        # create a single worker runtime
        worker_process = multiprocessing.Process(
            target=_create_worker_runtime,
            args=(worker_port, f'pod0/{i}', 'FastSlowExecutor'),
        )
        replica_processes.append(worker_process)
        worker_process.start()

        await asyncio.sleep(0.1)
        worker_ports.append(worker_port)

    await _activate_runtimes(head_port, worker_ports)

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port_expose),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port_expose}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port_expose, asyncio=True)
    input_docs = [Document(text='slow'), Document(text='fast')]
    responses = c.post('/', inputs=input_docs, request_size=1, return_results=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    head_process.terminate()
    for replica_process in replica_processes:
        replica_process.terminate()

    gateway_process.join()
    head_process.join()
    for replica_process in replica_processes:
        replica_process.join()

    assert len(response_list) == 2
    for response in response_list:
        assert len(response.docs) == 1

    assert response_list[0].docs[0].text == 'fast'
    assert response_list[1].docs[0].text == 'slow'

    assert gateway_process.exitcode == 0
    assert head_process.exitcode == 0
    for replica_process in replica_processes:
        assert replica_process.exitcode == 0


class NameChangeExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = runtime_args['name']

    @requests
    def foo(self, docs, **kwargs):
        print(f'{self.name} doc count {len(docs)}')
        docs.append(Document(text=self.name))
        return docs


class FastSlowExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            if doc.text == 'slow':
                time.sleep(1.0)


async def _activate_worker(head_port, worker_port, shard_id=None):
    # this would be done by the Pod, its adding the worker to the head
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity(
        'worker', '127.0.0.1', worker_port, shard_id=shard_id
    )
    GrpcConnectionPool.send_request_sync(activate_msg, f'127.0.0.1:{head_port}')


async def _create_worker(pod, port_generator, type='worker', executor=None):
    worker_port = port_generator()
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port, f'{pod}/{type}', executor)
    )
    worker_process.start()
    return worker_port, worker_process


def _create_worker_runtime(port, name='', executor=None):
    args = set_pea_parser().parse_args([])
    args.port_in = port
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_head_runtime(
    port, name='', polling='ANY', uses_before=None, uses_after=None
):
    args = set_pea_parser().parse_args([])
    args.port_in = port
    args.name = name
    args.polling = PollingType.ANY if polling == 'ANY' else PollingType.ALL
    if uses_before:
        args.uses_before_address = uses_before
    if uses_after:
        args.uses_after_address = uses_after

    with HeadRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(graph_description, pod_addresses, port_expose):
    with GRPCGatewayRuntime(
        set_gateway_parser().parse_args(
            [
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


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')


async def _activate_runtimes(head_port, worker_ports):
    for i, worker_port in enumerate(worker_ports):
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ready_or_shutdown_event=threading.Event(),
            ctrl_address=f'127.0.0.1:{worker_port}',
        )
        await _activate_worker(head_port, worker_port, shard_id=i)
