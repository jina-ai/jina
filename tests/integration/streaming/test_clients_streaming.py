import os
import time, asyncio

import pytest
from jina import Flow, Document, DocumentArray, Executor, requests


def sync_slow_gen():
    for i in range(4):
        print(f'in sync_slow_gen {i}')
        yield Document(id=i, tags={'input_gen': time.time()})
        time.sleep(1)


async def async_slow_gen():
    for i in range(4):
        print(f'in async_slow_gen {i}')
        yield Document(id=i, tags={'input_gen': time.time()})
        await asyncio.sleep(1)


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.tags['executor'] = time.time()
            print(f'in executor: {doc.id}')


def on_done(response, final_da: DocumentArray):
    for doc in response.docs:
        print(f'in on_done {doc.id}')
        doc.tags['on_done'] = time.time()
    final_da.extend(response.docs)


@pytest.mark.parametrize(
    'protocol, inputs',
    [
        # ('grpc', async_slow_gen),
        # pytest.param(
        #     'grpc',
        #     sync_slow_gen,
        #     marks=pytest.mark.xfail(
        #         reason='grpc client + sync generator with time.sleep is expected to fail'
        #     ),
        # ),
        # ('websocket', async_slow_gen),
        ('websocket', sync_slow_gen),
        # ('http', async_slow_gen),
        # ('http', sync_slow_gen),
    ],
)
def test_client_streaming_sync_gen(protocol, inputs):
    os.environ['JINA_LOG_LEVEL'] = 'ERROR'
    final_da = DocumentArray()
    with Flow(protocol=protocol, prefetch=1).add(uses=MyExecutor) as f:
        f.post(
            on='/',
            inputs=inputs,
            request_size=1,
            on_done=lambda response: on_done(response, final_da),
        )

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
