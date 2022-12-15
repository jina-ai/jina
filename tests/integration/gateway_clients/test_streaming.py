import asyncio
import copy
import multiprocessing
import os
import time
from datetime import datetime
from functools import partial
from typing import Dict

import pytest

from jina import Document, DocumentArray
from jina.clients import Client
from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.serve import networking
from jina.serve.runtimes.gateway import GatewayRuntime

INPUT_LEN = 4
INPUT_GEN_SLEEP_TIME = 1
SLOW_EXECUTOR_SLEEP_TIME = 5


@pytest.fixture
def simple_graph_dict_slow():
    return {
        'start-gateway': ['slow-executor'],
        'slow-executor': ['end-gateway'],
    }


@pytest.fixture
def simple_graph_dict_fast():
    return {
        'start-gateway': ['fast-executor'],
        'slow-executor': ['end-gateway'],
    }


@pytest.fixture
def simple_graph_dict_indexer():
    return {
        'start-gateway': ['indexer-executor'],
        'slow-executor': ['end-gateway'],
    }


class DummyMockConnectionPool:
    def send_discover_endpoint(self, *args, **kwargs):
        async def task_wrapper():
            from jina import __default_endpoint__
            from jina.proto import jina_pb2

            ep = jina_pb2.EndpointsProto()
            ep.endpoints.extend([__default_endpoint__])
            return ep, None

        return asyncio.create_task(task_wrapper())

    def send_requests_once(
        self,
        requests,
        deployment: str,
        head: bool,
        metadata: dict = None,
        shard_id=None,
        endpoint: str = None,
        timeout: float = 1.0,
        retries: int = -1,
    ) -> asyncio.Task:
        assert head
        request = requests[0]

        if not hasattr(self, '_docs'):
            self._docs = DocumentArray()

        async def _compute_response():
            response_msg = copy.deepcopy(request)
            exec_endpoint = request.header.exec_endpoint
            new_docs = DocumentArray()
            await asyncio.sleep(0.1)
            if deployment == 'indexer-executor':
                if exec_endpoint == '/index':
                    time.sleep(0.1)
                    self._docs.extend(request.docs)
                else:
                    docs = response_msg.docs
                    docs.clear()
                    docs.extend(
                        DocumentArray(Document(tags={'ids': self._docs[:, 'id']}))
                    )
                    response_msg.data.docs = docs
                return response_msg
            else:
                if deployment == 'slow-executor':
                    await asyncio.sleep(SLOW_EXECUTOR_SLEEP_TIME)
                for doc in request.docs:
                    new_doc = Document(doc, copy=True)
                    new_doc.tags['executor'] = time.time()
                    print(
                        f'in {deployment}, {new_doc.id} => time: {readable_time_from(new_doc.tags["executor"])}, {new_doc.tags["executor"]}',
                        flush=True,
                    )
                    new_docs.append(new_doc)

                docs = response_msg.docs
                docs.clear()
                docs.extend(new_docs)
                response_msg.data.docs = docs
                return response_msg

        async def task_wrapper():
            response_msg = await _compute_response()
            return response_msg, {}

        return asyncio.create_task(task_wrapper())


def readable_time_from(t):
    return datetime.utcfromtimestamp(t).strftime('%M:%S:%f')


def get_document(i, name):
    t = time.time()
    print(f'in {name} {i}, time: {readable_time_from(t)}, {t}', flush=True)
    return Document(id=f'id-{i}', tags={'input_gen': t})


def blocking_gen():
    """Fast synchronous client generator"""
    for i in range(INPUT_LEN):
        yield get_document(i, name='blocking_gen')
        time.sleep(0.1)


async def async_gen():
    """Fast async client generator"""
    for i in range(INPUT_LEN):
        yield get_document(i, name='async_gen')
        await asyncio.sleep(0.1)


def slow_blocking_gen():
    """Slow synchronous client generator"""
    for i in range(INPUT_LEN):
        yield get_document(i, name='slow_blocking_gen')
        time.sleep(INPUT_GEN_SLEEP_TIME)


async def slow_async_gen():
    """Slow async client generator"""
    for i in range(INPUT_LEN):
        yield get_document(i, name='slow_async_gen')
        await asyncio.sleep(INPUT_GEN_SLEEP_TIME)


def on_done(response, final_da: DocumentArray):
    docs = response.docs
    for doc in docs:
        doc.tags['on_done'] = time.time()
        print(
            f'in on_done {doc.id}, time: {readable_time_from(doc.tags["on_done"])}',
            flush=True,
        )
    final_da.extend(docs)


def create_runtime(graph_dict: Dict, protocol: str, port: int, prefetch: int = 0):
    import json

    graph_description = json.dumps(graph_dict)

    args = set_gateway_parser().parse_args(
        [
            '--port',
            f'{port}',
            '--graph-description',
            f'{graph_description}',
            '--deployments-addresses',
            '{}',
            '--prefetch',
            f'{prefetch}',
            '--protocol',
            protocol,
        ]
    )
    with GatewayRuntime(args) as runtime:
        runtime.run_forever()


@pytest.mark.parametrize(
    'protocol, inputs',
    [
        ('grpc', slow_async_gen),
        pytest.param(
            'grpc',
            slow_blocking_gen,
            marks=pytest.mark.skip(
                reason='grpc client + sync generator with time.sleep is expected to fail'
            ),
        ),
        ('websocket', slow_async_gen),
        ('websocket', slow_blocking_gen),
        ('http', slow_async_gen),
        ('http', slow_blocking_gen),
    ],
)
def test_disable_prefetch_slow_client_fast_executor(
    protocol, inputs, monkeypatch, simple_graph_dict_fast
):
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_discover_endpoint',
        DummyMockConnectionPool.send_discover_endpoint,
    )
    port = random_port()

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': simple_graph_dict_fast,
        },
    )
    p.start()
    time.sleep(1.0)

    final_da = DocumentArray()

    client = Client(protocol=protocol, port=port)
    client.post(
        on='/',
        inputs=inputs,
        request_size=1,
        on_done=lambda response: on_done(response, final_da),
    )
    p.terminate()
    p.join()
    assert len(final_da) == INPUT_LEN
    # Since the input_gen is slow, order will always be gen -> exec -> on_done for every request
    assert final_da['id-0'].tags['input_gen'] < final_da['id-0'].tags['executor']
    assert final_da['id-0'].tags['executor'] < final_da['id-0'].tags['on_done']
    assert final_da['id-0'].tags['on_done'] < final_da['id-1'].tags['input_gen']
    assert final_da['id-1'].tags['input_gen'] < final_da['id-1'].tags['executor']
    assert final_da['id-1'].tags['executor'] < final_da['id-1'].tags['on_done']
    assert final_da['id-1'].tags['on_done'] < final_da['id-2'].tags['input_gen']
    assert final_da['id-2'].tags['input_gen'] < final_da['id-2'].tags['executor']
    assert final_da['id-2'].tags['executor'] < final_da['id-2'].tags['on_done']
    assert final_da['id-2'].tags['on_done'] < final_da['id-3'].tags['input_gen']
    assert final_da['id-3'].tags['input_gen'] < final_da['id-3'].tags['executor']
    assert final_da['id-3'].tags['executor'] < final_da['id-3'].tags['on_done']


@pytest.mark.parametrize(
    'protocol, inputs',
    [
        ('grpc', async_gen),
        ('grpc', blocking_gen),
        ('websocket', async_gen),
        ('websocket', blocking_gen),
        ('http', async_gen),
        ('http', blocking_gen),
    ],
)
def test_disable_prefetch_fast_client_slow_executor(
    protocol, inputs, monkeypatch, simple_graph_dict_slow
):
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_discover_endpoint',
        DummyMockConnectionPool.send_discover_endpoint,
    )
    port = random_port()
    final_da = DocumentArray()
    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': simple_graph_dict_slow,
        },
    )
    p.start()
    time.sleep(1.0)
    client = Client(protocol=protocol, port=port)
    client.post(
        on='/',
        inputs=inputs,
        request_size=1,
        on_done=lambda response: on_done(response, final_da),
    )
    p.terminate()
    p.join()

    assert len(final_da) == INPUT_LEN
    # since Executor is slow, all client inputs should be read before 1st request exits from Executor.
    assert (
        final_da['id-0'].id < final_da['id-1'].id
    ), f'ids are not ordered with times {final_da["id-0"].tags["input_gen"]} and {final_da["id-1"].tags["input_gen"]}'
    assert (
        final_da['id-1'].id < final_da['id-2'].id
    ), f'ids are not ordered with times {final_da["id-1"].tags["input_gen"]} and {final_da["id-2"].tags["input_gen"]}'
    assert (
        final_da['id-2'].id < final_da['id-3'].id
    ), f'ids are not ordered with times {final_da["id-2"].tags["input_gen"]} and {final_da["id-3"].tags["input_gen"]}'
    assert final_da['id-0'].tags['input_gen'] < final_da['id-1'].tags['input_gen']
    assert final_da['id-1'].tags['input_gen'] < final_da['id-2'].tags['input_gen']
    assert final_da['id-2'].tags['input_gen'] < final_da['id-3'].tags['input_gen']
    assert final_da['id-3'].tags['input_gen'] < final_da['id-0'].tags['executor']
    # At least 1 request should reache `on_done` before all requests are processed in the Executor.
    # Validates that the requests are not pending at the Executor
    first_on_done_time = min(i.tags['on_done'] for i in final_da)
    last_executor_time = max(i.tags['executor'] for i in final_da)
    assert first_on_done_time < last_executor_time


@pytest.mark.parametrize('prefetch', [0, 5])
@pytest.mark.parametrize('protocol', ['websocket', 'http', 'grpc'])
@pytest.mark.parametrize('use_stream', [True, False])
def test_multiple_clients(prefetch, protocol, monkeypatch, simple_graph_dict_indexer, use_stream):
    GOOD_CLIENTS = 5
    GOOD_CLIENT_NUM_DOCS = 20
    MALICIOUS_CLIENT_NUM_DOCS = 50

    def get_document(i):
        return Document(
            id=f'{multiprocessing.current_process().name}_{i}',
            text=str(bytes(bytearray(os.urandom(512 * 4)))),
        )

    async def good_client_gen():
        for i in range(GOOD_CLIENT_NUM_DOCS):
            yield get_document(i)
            await asyncio.sleep(0.1)

    async def malicious_client_gen():
        for i in range(1000, 1000 + MALICIOUS_CLIENT_NUM_DOCS):
            yield get_document(i)

    def client(gen, port):
        Client(protocol=protocol, port=port).post(
            on='/index', inputs=gen, request_size=1, stream=use_stream
        )

    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_discover_endpoint',
        DummyMockConnectionPool.send_discover_endpoint,
    )
    port = random_port()

    pool = []
    runtime_process = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': simple_graph_dict_indexer,
            'prefetch': prefetch,
        },
    )
    runtime_process.start()
    time.sleep(1.0)
    # We have 5 good clients connecting to the same gateway. They have controlled requests.
    # Each client sends `GOOD_CLIENT_NUM_DOCS` (20) requests and sleeps after each request.
    for i in range(GOOD_CLIENTS):
        cp = multiprocessing.Process(
            target=partial(client, good_client_gen, port),
            name=f'goodguy_{i}',
        )
        cp.start()
        pool.append(cp)

    # and 1 malicious client, sending lot of requests (trying to block others)
    cp = multiprocessing.Process(
        target=partial(client, malicious_client_gen, port),
        name='badguy',
    )
    cp.start()
    pool.append(cp)

    for p in pool:
        p.join()

    order_of_ids = list(
        Client(protocol=protocol, port=port)
        .post(on='/status', inputs=[Document()], stream=use_stream)[0]
        .tags['ids']
    )
    # There must be total 150 docs indexed.

    runtime_process.terminate()
    runtime_process.join()
    assert (
        len(order_of_ids)
        == GOOD_CLIENTS * GOOD_CLIENT_NUM_DOCS + MALICIOUS_CLIENT_NUM_DOCS
    )

    """
    If prefetch is set, each Client is allowed (max) 5 requests at a time.
    Since requests are controlled, `badguy` has to do the last 20 requests.

    If prefetch is disabled, clients can freeflow requests. No client is blocked.
    Hence last 20 requests go from `goodguy`.
    (Ideally last 30 requests should be validated, to avoid flaky CI, we test last 20)

    When there are no rules, badguy wins! With rule, you find balance in the world.
    """
    if protocol == 'http':
        # There's no prefetch for http.
        assert set(map(lambda x: x.split('_')[0], order_of_ids[-20:])) == {'goodguy'}
    elif prefetch == 5:
        assert set(map(lambda x: x.split('_')[0], order_of_ids[-20:])) == {'badguy'}
    elif prefetch == 0:
        assert set(map(lambda x: x.split('_')[0], order_of_ids[-20:])) == {'goodguy'}
