import asyncio
import json
import multiprocessing
import threading
import time
from collections import defaultdict

import grpc
import pytest

from jina import Client, Document, DocumentArray, Executor, requests
from jina.clients.request import request_generator
from jina.enums import PollingType
from jina.parsers import set_gateway_parser
from jina.proto import jina_pb2_grpc
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.head import HeadRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import _generate_pod_args


@pytest.mark.asyncio
# test gateway, head and worker runtime by creating them manually in the most simple configuration
async def test_runtimes_trivial_topology(port_generator):
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
    connection_list_dict = {'0': [f'127.0.0.1:{worker_port}']}

    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port, connection_list_dict)
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

        # create worker
        worker_port, worker_process = await _create_worker(pod, port_generator)
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ready_or_shutdown_event=threading.Event(),
            ctrl_address=f'127.0.0.1:{worker_port}',
        )
        runtime_processes.append(worker_process)

        # create head
        head_port = port_generator()
        pod_addresses += f'"{pod}": ["0.0.0.0:{head_port}"],'
        connection_list_dict = {'0': [f'127.0.0.1:{worker_port}']}
        head_process = multiprocessing.Process(
            target=_create_head_runtime,
            args=(
                head_port,
                connection_list_dict,
                f'{pod}/head',
                'ANY',
                f'127.0.0.1:{uses_before_port}' if uses_before else None,
                f'127.0.0.1:{uses_after_port}' if uses_after else None,
            ),
        )
        runtime_processes.append(head_process)
        head_process.start()

        await asyncio.sleep(0.1)

    # remove last comma
    pod_addresses = pod_addresses[:-1]
    pod_addresses += '}'
    port = port_generator()

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(json.dumps(complete_graph_dict), pod_addresses, port),
    )
    gateway_process.start()

    await asyncio.sleep(0.1)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    # send requests to the gateway
    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
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
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create the shards
    shard_processes = []
    worker_ports = []
    connection_list_dict = defaultdict(list)
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
        connection_list_dict[i].append(f'127.0.0.1:{worker_port}')

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime,
        args=(head_port, connection_list_dict, 'head', polling),
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
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
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
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create the shards
    replica_processes = []
    worker_ports = []
    connection_list_dict = defaultdict(list)
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
        connection_list_dict[0].append(f'127.0.0.1:{worker_port}')

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port, connection_list_dict, 'head')
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
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
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
async def test_runtimess_with_executor(port_generator):
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

    # create some shards
    connection_list_dict = defaultdict(list)
    worker_ports = []
    for i in range(10):
        # create worker
        worker_port, worker_process = await _create_worker(
            'pod0', port_generator, type=f'shards/{i}', executor='NameChangeExecutor'
        )
        runtime_processes.append(worker_process)
        await asyncio.sleep(0.1)
        worker_ports.append(worker_port)
        connection_list_dict[i].append(f'127.0.0.1:{worker_port}')

    head_process = multiprocessing.Process(
        target=_create_head_runtime,
        args=(
            head_port,
            connection_list_dict,
            f'pod0/head',
            'ALL',
            f'127.0.0.1:{uses_before_port}',
            f'127.0.0.1:{uses_after_port}',
        ),
    )
    runtime_processes.append(head_process)
    head_process.start()

    # create a single gateway runtime
    port = port_generator()
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port),
    )
    gateway_process.start()
    runtime_processes.append(gateway_process)

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
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


@pytest.mark.asyncio
async def test_runtimes_gateway_worker_direct_connection(port_generator):
    worker_port = port_generator()
    port = port_generator()
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
        args=(graph_description, pod_addresses, port),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
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
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{head_port}"]}}'

    # create the shards
    replica_processes = []
    worker_ports = []
    connection_list_dict = defaultdict(list)
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
        connection_list_dict[i].append(f'127.0.0.1:{worker_port}')

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime, args=(head_port, connection_list_dict, 'head')
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
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    c = Client(host='localhost', port=port, asyncio=True)
    input_docs = [Document(text='slow'), Document(text='fast')]
    responses = c.post('/', inputs=input_docs, request_size=1, return_responses=True)
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


@pytest.mark.asyncio
# test gateway to gateway communication
# this mimics using an external executor, fronted by a gateway
async def test_runtimes_gateway_to_gateway(port_generator):
    worker_port = port_generator()
    external_gateway_port = port_generator()
    port = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{external_gateway_port}"]}}'
    worker_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    # create a single worker runtime
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port,)
    )
    worker_process.start()

    # create the "external" gateway runtime
    external_gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, worker_addresses, external_gateway_port),
    )
    external_gateway_process.start()

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port),
    )
    gateway_process.start()

    await asyncio.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{external_gateway_port}',
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

    # send requests to the gateway
    c = Client(host='localhost', port=port, asyncio=True)
    responses = c.post('/', inputs=async_inputs, request_size=1, return_responses=True)
    response_list = []
    async for response in responses:
        response_list.append(response)

    # clean up runtimes
    gateway_process.terminate()
    external_gateway_process.terminate()
    worker_process.terminate()

    gateway_process.join()
    external_gateway_process.join()
    worker_process.join()

    assert len(response_list) == 20
    assert len(response_list[0].docs) == 1

    assert gateway_process.exitcode == 0
    assert external_gateway_process.exitcode == 0
    assert worker_process.exitcode == 0


class NameChangeExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = runtime_args['name']

    @requests
    def foo(self, docs, **kwargs):
        docs.append(Document(text=self.name))
        return docs


class FastSlowExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            if doc.text == 'slow':
                time.sleep(1.0)


async def _create_worker(pod, port_generator, type='worker', executor=None):
    worker_port = port_generator()
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port, f'{pod}/{type}', executor)
    )
    worker_process.start()
    return worker_port, worker_process


def _create_worker_runtime(port, name='', executor=None):
    args = _generate_pod_args()
    args.port = port
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_head_runtime(
    port,
    connection_list_dict,
    name='',
    polling='ANY',
    uses_before=None,
    uses_after=None,
    retries=-1,
):
    args = _generate_pod_args()
    args.port = port
    args.name = name
    args.retries = retries
    args.polling = PollingType.ANY if polling == 'ANY' else PollingType.ALL
    if uses_before:
        args.uses_before_address = uses_before
    if uses_after:
        args.uses_after_address = uses_after
    args.connection_list = json.dumps(connection_list_dict)

    with HeadRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(
    graph_description, pod_addresses, port, protocol='grpc', retries=-1
):
    with GatewayRuntime(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
                '--retries',
                str(retries),
                '--protocol',
                protocol,
            ]
        )
    ) as runtime:
        runtime.run_forever()


async def async_inputs():
    for _ in range(20):
        yield Document(text='client0-Request')


@pytest.mark.asyncio
async def test_head_runtime_with_offline_shards(port_generator):
    head_port = port_generator()

    # create the shards
    shard_processes = []
    worker_ports = []
    connection_list_dict = defaultdict(list)
    for i in range(2):
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
        connection_list_dict[i].append(f'127.0.0.1:{worker_port}')

    # create a failing connection/port
    worker_port = port_generator()
    worker_ports.append(worker_port)
    connection_list_dict[i + 1].append(f'127.0.0.1:{worker_port}')

    # create a single head runtime
    head_process = multiprocessing.Process(
        target=_create_head_runtime,
        args=(head_port, connection_list_dict, 'head', 'ALL'),
    )
    head_process.start()

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=1.0,
        ctrl_address=f'0.0.0.0:{head_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    with grpc.insecure_channel(
        f'0.0.0.0:{head_port}',
        options=GrpcConnectionPool.get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        _, call = stub.process_single_data.with_call(
            list(request_generator('/index', DocumentArray([Document(text='abc')])))[0]
        )
        call_metadata = dict(call.trailing_metadata())
        assert len(call_metadata) == 2
        assert call_metadata['total_shards'] == '3'
        assert call_metadata['failed_shards'] == '1'

    # clean up runtimes
    head_process.terminate()
    for shard_process in shard_processes:
        shard_process.terminate()

    head_process.join()
    for shard_process in shard_processes:
        shard_process.join()


def test_runtime_slow_processing_readiness(port_generator):
    class SlowProcessingExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            time.sleep(10)

    worker_port = port_generator()
    # create a single worker runtime
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime,
        args=(worker_port, f'pod0', 'SlowProcessingExecutor'),
    )
    try:
        worker_process.start()
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{worker_port}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        def _send_messages():
            with grpc.insecure_channel(
                f'0.0.0.0:{worker_port}',
                options=GrpcConnectionPool.get_default_grpc_options(),
            ) as channel:
                stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
                resp, _ = stub.process_single_data.with_call(
                    list(request_generator('/', DocumentArray([Document(text='abc')])))[
                        0
                    ]
                )
                assert resp.docs[0].text == 'abc'

        send_message_process = multiprocessing.Process(target=_send_messages)
        send_message_process.start()

        for _ in range(50):
            is_ready = WorkerRuntime.is_ready(f'0.0.0.0:{worker_port}')
            assert is_ready
            time.sleep(0.5)
    except Exception:
        raise
    finally:
        worker_process.terminate()
        send_message_process.terminate()
        worker_process.join()
        send_message_process.join()
        assert worker_process.exitcode == 0
        assert send_message_process.exitcode == 0
