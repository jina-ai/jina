import os
import time, asyncio
from typing import List
from datetime import datetime
from functools import partial
from multiprocessing import Process, current_process

import pytest
from jina import Flow, Document, DocumentArray, Executor, requests, Client

INPUT_LEN = 4
INPUT_GEN_SLEEP_TIME = 1
SLOW_EXECUTOR_SLEEP_TIME = 5


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


class FastExecutor(Executor):
    """Fast Executor"""

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.tags['executor'] = time.time()
            print(
                f'in FastExecutor: {doc.id}, time: {readable_time_from(doc.tags["executor"])}, {doc.tags["executor"]}',
                flush=True,
            )


class SlowExecutor(Executor):
    """Slow Executor (sleeps DELAYED_EXECUTOR_SLEEP_TIME secs b/w each req)"""

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        time.sleep(SLOW_EXECUTOR_SLEEP_TIME)
        for doc in docs:
            doc.tags['executor'] = time.time()
            print(
                f'in SlowExecutor: {doc.id}, time: {readable_time_from(doc.tags["executor"])}, {doc.tags["executor"]}',
                flush=True,
            )


def on_done(response, final_da: DocumentArray):
    print(f' receiving response {response._pb_body.request_id}')
    for doc in response.docs:
        doc.tags['on_done'] = time.time()
        print(
            f'in on_done {doc.id}, time: {readable_time_from(doc.tags["on_done"])}, {doc.tags["on_done"]}',
            flush=True,
        )
    final_da.extend(response.docs)


@pytest.mark.parametrize('grpc_data_requests', [False, True])
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
    grpc_data_requests, protocol, inputs
):
    print(
        f'\n\nRunning disable prefetch, slow client, fast Executor test for \n'
        f'protocol: {protocol}, input: {inputs.__name__}, grpc_data_req: {grpc_data_requests}'
    )
    final_da = DocumentArray()
    with Flow(protocol=protocol, grpc_data_requests=grpc_data_requests).add(
        uses=FastExecutor
    ) as f:
        f.post(
            on='/',
            inputs=inputs,
            request_size=1,
            on_done=lambda response: on_done(response, final_da),
        )

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


@pytest.mark.parametrize('grpc_data_requests', [True, False])
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
    grpc_data_requests, protocol, inputs
):
    print(
        f'\n\nRunning disable prefetch, fast client, slow Executor test for \n'
        f'protocol: {protocol}, input: {inputs.__name__}, grpc_data_req: {grpc_data_requests}'
    )
    final_da = DocumentArray()
    with Flow(protocol=protocol, grpc_data_requests=grpc_data_requests).add(
        uses=SlowExecutor
    ) as f:
        f.post(
            on='/',
            inputs=inputs,
            request_size=1,
            on_done=lambda response: on_done(response, final_da),
        )

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


class Indexer(Executor):
    docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        time.sleep(0.1)
        self.docs.extend(docs)

    @requests(on='/status')
    def status(self, **kwargs):
        # returns ids of all docs in tags
        return DocumentArray(Document(tags={'ids': self.docs.get_attributes('id')}))


@pytest.mark.parametrize('prefetch', [0, 5])
@pytest.mark.parametrize('protocol', ['websocket', 'http', 'grpc'])
@pytest.mark.parametrize('grpc_data_requests', [False, True])
def test_multiple_clients(prefetch, protocol, grpc_data_requests):
    os.environ['JINA_LOG_LEVEL'] = 'INFO'
    GOOD_CLIENTS = 5
    GOOD_CLIENT_NUM_DOCS = 20
    MALICIOUS_CLIENT_NUM_DOCS = 50

    def get_document(i):
        return Document(
            id=f'{current_process().name}_{i}',
            buffer=bytes(bytearray(os.urandom(512 * 4))),
        )

    async def good_client_gen():
        for i in range(GOOD_CLIENT_NUM_DOCS):
            yield get_document(i)
            await asyncio.sleep(0.1)

    async def malicious_client_gen():
        for i in range(1000, 1000 + MALICIOUS_CLIENT_NUM_DOCS):
            yield get_document(i)

    def client(gen, port, protocol):
        Client(protocol=protocol, port=port).post(
            on='/index', inputs=gen, request_size=1
        )

    pool: List[Process] = []
    f = Flow(
        protocol=protocol, prefetch=prefetch, grpc_data_requests=grpc_data_requests
    ).add(uses=Indexer)
    with f:
        # We have 5 good clients connecting to the same gateway. They have controlled requests.
        # Each client sends `GOOD_CLIENT_NUM_DOCS` (20) requests and sleeps after each request.
        for i in range(GOOD_CLIENTS):
            p = Process(
                target=partial(client, good_client_gen, f.port_expose, protocol),
                name=f'goodguy_{i}',
            )
            p.start()
            pool.append(p)

        # and 1 malicious client, sending lot of requests (trying to block others)
        p = Process(
            target=partial(client, malicious_client_gen, f.port_expose, protocol),
            name='badguy',
        )
        p.start()
        pool.append(p)

        for p in pool:
            p.join()

        order_of_ids = list(
            Client(protocol=protocol, port=f.port_expose)
            .post(on='/status', inputs=[Document()], return_results=True)[0]
            .docs[0]
            .tags['ids']
        )
        # There must be total 150 docs indexed.
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
            assert set(map(lambda x: x.split('_')[0], order_of_ids[-20:])) == {
                'goodguy'
            }
        elif prefetch == 5:
            assert set(map(lambda x: x.split('_')[0], order_of_ids[-20:])) == {'badguy'}
        elif prefetch == 0:
            assert set(map(lambda x: x.split('_')[0], order_of_ids[-20:])) == {
                'goodguy'
            }
