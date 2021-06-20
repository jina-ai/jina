import asyncio
import time

import numpy as np
import pytest

from jina import Document, Flow
from jina.flow.asyncio import AsyncFlow
from jina.logging.profile import TimeContext
from jina.types.document.generators import from_ndarray
from jina.types.request import Response
from tests import validate_callback

num_docs = 5


def validate(req):
    assert len(req.docs) == num_docs
    assert req.docs[0].blob.ndim == 1


def documents(start_index, end_index):
    for i in range(start_index, end_index):
        with Document() as doc:
            doc.text = 'this is text'
            doc.tags['id'] = 'id in tags'
            doc.tags['inner_dict'] = {'id': 'id in inner_dict'}
            with Document() as chunk:
                chunk.text = 'text in chunk'
                chunk.tags['id'] = 'id in chunk tags'
            doc.chunks.append(chunk)
        yield doc


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
@pytest.mark.parametrize('flow_cls', [Flow, AsyncFlow])
async def test_run_async_flow(protocol, mocker, flow_cls):
    r_val = mocker.Mock()
    with flow_cls(protocol=protocol, asyncio=True).add() as f:
        async for r in f.index(
            from_ndarray(np.random.random([num_docs, 4])), on_done=r_val
        ):
            assert isinstance(r, Response)
    validate_callback(r_val, validate)


async def async_input_function():
    for _ in range(num_docs):
        yield Document(content=np.random.random([4]))
        await asyncio.sleep(0.1)


async def async_input_function2():
    for _ in range(num_docs):
        yield Document(content=np.random.random([4]))
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'inputs',
    [
        async_input_function,
        async_input_function(),
        async_input_function2(),
        async_input_function2,
    ],
)
async def test_run_async_flow_async_input(inputs, mocker):
    r_val = mocker.Mock()
    with AsyncFlow(asyncio=True).add() as f:
        async for r in f.index(inputs, on_done=r_val):
            assert isinstance(r, Response)
    validate_callback(r_val, validate)


async def run_async_flow_5s(protocol):
    # WaitDriver pause 5s makes total roundtrip ~5s
    from jina import Executor, requests

    class Wait5s(Executor):
        @requests
        def foo(self, **kwargs):
            print('im called!')
            time.sleep(5)

    with Flow(protocol=protocol, asyncio=True).add(uses=Wait5s) as f:
        async for r in f.index(
            from_ndarray(np.random.random([num_docs, 4])),
            on_done=validate,
        ):
            assert isinstance(r, Response)


async def sleep_print():
    # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')


async def concurrent_main(protocol):
    # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(protocol), sleep_print())


async def sequential_main(protocol):
    # about 10s; with some dispatch cost , usually at <12s
    await run_async_flow_5s(protocol)
    await sleep_print()


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
async def test_run_async_flow_other_task_sequential(protocol):
    with TimeContext('sequential await') as t:
        await sequential_main(protocol)

    assert t.duration >= 10


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
async def test_run_async_flow_other_task_concurrent(protocol):
    with TimeContext('concurrent await') as t:
        await concurrent_main(protocol)

    # some dispatch cost, can't be just 5s, usually at 7~8s, but must <10s
    assert t.duration < 10


@pytest.mark.asyncio
@pytest.mark.parametrize('return_results', [False])
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
@pytest.mark.parametrize('flow_cls', [Flow, AsyncFlow])
async def test_return_results_async_flow(return_results, protocol, flow_cls):
    with flow_cls(
        protocol=protocol, asyncio=True, return_results=return_results
    ).add() as f:
        async for r in f.index(from_ndarray(np.random.random([10, 2]))):
            assert isinstance(r, Response)


@pytest.mark.asyncio
@pytest.mark.parametrize('return_results', [False, True])
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
@pytest.mark.parametrize('flow_api', ['delete', 'index', 'update', 'search'])
@pytest.mark.parametrize('flow_cls', [Flow, AsyncFlow])
async def test_return_results_async_flow_crud(
    return_results, protocol, flow_api, flow_cls
):
    with flow_cls(
        protocol=protocol, asyncio=True, return_results=return_results
    ).add() as f:
        async for r in getattr(f, flow_api)(documents(0, 10)):
            assert isinstance(r, Response)


@pytest.mark.asyncio
@pytest.mark.parametrize('flow_cls', [Flow, AsyncFlow])
async def test_async_flow_empty_data(flow_cls):
    from jina import Executor, requests

    class MyExec(Executor):
        @requests
        def foo(self, parameters, **kwargs):
            assert parameters['hello'] == 'world'

    with flow_cls(asyncio=True).add(uses=MyExec) as f:
        async for r in f.post('/hello', parameters={'hello': 'world'}):
            assert isinstance(r, Response)
