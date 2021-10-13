import os
import time, asyncio

import pytest
from jina import Flow, Document, DocumentArray, Executor, requests

INPUT_LEN = 4
INPUT_GEN_SLEEP_TIME = 1
SLOW_EXECUTOR_SLEEP_TIME = 3


def get_document(i):
    return Document(id=i, tags={'input_gen': time.time()})


def gen():
    """Fast synchronous client generator"""
    for i in range(INPUT_LEN):
        print(f'in gen {i}')
        yield get_document(i)
        time.sleep(0.1)


async def async_gen():
    """Fast async client generator"""
    for i in range(INPUT_LEN):
        print(f'in async_gen {i}')
        yield get_document(i)
        await asyncio.sleep(0.1)


def slow_blocking_gen():
    """Slow synchronous client generator"""
    for i in range(INPUT_LEN):
        print(f'in sync_slow_gen {i}')
        yield get_document(i)
        time.sleep(INPUT_GEN_SLEEP_TIME)


async def slow_async_gen():
    """Slow async client generator"""
    for i in range(INPUT_LEN):
        print(f'in async_slow_gen {i}')
        yield get_document(i)
        await asyncio.sleep(INPUT_GEN_SLEEP_TIME)


class FastExecutor(Executor):
    """Fast Executor"""

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.tags['executor'] = time.time()
            print(f'in FastExecutor: {doc.id}')


class SlowExecutor(Executor):
    """Slow Executor (sleeps DELAYED_EXECUTOR_SLEEP_TIME secs b/w each req)"""

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        time.sleep(SLOW_EXECUTOR_SLEEP_TIME)
        for doc in docs:
            doc.tags['executor'] = time.time()
            print(f'in SlowExecutor: {doc.id}')


def on_done(response, final_da: DocumentArray):
    for doc in response.docs:
        print(f'in on_done {doc.id}')
        doc.tags['on_done'] = time.time()
    final_da.extend(response.docs)


@pytest.mark.parametrize('grpc_data_requests', [False, True])
@pytest.mark.parametrize(
    'protocol, inputs',
    [
        ('grpc', slow_async_gen),
        pytest.param(
            'grpc',
            slow_blocking_gen,
            marks=pytest.mark.xfail(
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
    os.environ['JINA_LOG_LEVEL'] = 'ERROR'
    final_da = DocumentArray()
    with Flow(protocol=protocol, prefetch=0, grpc_data_requests=grpc_data_requests).add(
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
    assert (
        final_da[0].tags['input_gen']
        < final_da[0].tags['executor']
        < final_da[0].tags['on_done']
        < final_da[1].tags['input_gen']
        < final_da[1].tags['executor']
        < final_da[1].tags['on_done']
        < final_da[2].tags['input_gen']
        < final_da[2].tags['executor']
        < final_da[2].tags['on_done']
        < final_da[3].tags['input_gen']
        < final_da[3].tags['executor']
        < final_da[3].tags['on_done']
    )


@pytest.mark.parametrize('grpc_data_requests', [False, True])
@pytest.mark.parametrize(
    'protocol, inputs',
    [
        ('grpc', async_gen),
        ('grpc', gen),
        ('websocket', async_gen),
        ('websocket', gen),
        ('http', async_gen),
        ('http', gen),
    ],
)
def test_disable_prefetch_fast_client_slow_executor(
    grpc_data_requests, protocol, inputs
):
    print(
        f'\n\nRunning disable prefetch, fast client, slow Executor test for \n'
        f'protocol: {protocol}, input: {inputs.__name__}, grpc_data_req: {grpc_data_requests}'
    )
    os.environ['JINA_LOG_LEVEL'] = 'ERROR'
    final_da = DocumentArray()
    with Flow(protocol=protocol, prefetch=0, grpc_data_requests=grpc_data_requests).add(
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
        final_da[0].tags['input_gen']
        < final_da[1].tags['input_gen']
        < final_da[2].tags['input_gen']
        < final_da[3].tags['input_gen']
        < final_da[0].tags['executor']
    )
    # At least 1 request should reache `on_done` before all requests are processed in the Executor.
    # Validates that the requests are not pending at the Executor
    first_on_done_time = min(i.tags['on_done'] for i in final_da)
    last_executor_time = max(i.tags['executor'] for i in final_da)
    assert first_on_done_time < last_executor_time
