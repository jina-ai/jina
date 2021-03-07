import asyncio

import numpy as np
import pytest

from jina import Document
from jina.flow.asyncio import AsyncFlow
from jina.logging.profile import TimeContext
from jina.types.request import Response

from tests import validate_callback

num_docs = 5


def validate(req):
    assert len(req.docs) == num_docs
    assert req.docs[0].blob.ndim == 1


# TODO(Deepankar): with `restful: True` few of the asyncio tests are flaky.
# Though it runs fine locally, results in - `RuntimeError - Event loop closed` in CI (Disabling for now)


def documents(start_index, end_index):
    for i in range(start_index, end_index):
        with Document() as doc:
            doc.text = 'this is text'
            doc.tags['id'] = 'id in tags'
            doc.tags['inner_dict'] = {'id': 'id in inner_dict'}
            with Document() as chunk:
                chunk.text = 'text in chunk'
                chunk.tags['id'] = 'id in chunk tags'
            doc.chunks.add(chunk)
        yield doc


@pytest.mark.asyncio
@pytest.mark.parametrize('restful', [False])
async def test_run_async_flow(restful, mocker):
    r_val = mocker.Mock()
    with AsyncFlow(restful=restful).add() as f:
        async for r in f.index_ndarray(np.random.random([num_docs, 4]), on_done=r_val):
            assert isinstance(r, Response)
    validate_callback(r_val, validate)


async def async_input_function():
    for _ in range(num_docs):
        yield np.random.random([4])
        await asyncio.sleep(0.1)


async def async_input_function2():
    for _ in range(num_docs):
        yield Document(content=np.random.random([4]))
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
@pytest.mark.parametrize('restful', [False])
@pytest.mark.parametrize(
    'inputs',
    [
        async_input_function,
        async_input_function(),
        async_input_function2(),
        async_input_function2,
    ],
)
async def test_run_async_flow_async_input(restful, inputs, mocker):
    r_val = mocker.Mock()
    with AsyncFlow(restful=restful).add() as f:
        async for r in f.index(inputs, on_done=r_val):
            assert isinstance(r, Response)
    validate_callback(r_val, validate)


async def run_async_flow_5s(restful):
    # WaitDriver pause 5s makes total roundtrip ~5s
    with AsyncFlow(restful=restful).add(uses='- !WaitDriver {}') as f:
        async for r in f.index_ndarray(
            np.random.random([num_docs, 4]), on_done=validate
        ):
            assert isinstance(r, Response)


async def sleep_print():
    # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')


async def concurrent_main(restful):
    # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(restful), sleep_print())


async def sequential_main(restful):
    # about 10s; with some dispatch cost , usually at <12s
    await run_async_flow_5s(restful)
    await sleep_print()


@pytest.mark.asyncio
@pytest.mark.parametrize('restful', [False])
async def test_run_async_flow_other_task_sequential(restful):
    with TimeContext('sequential await') as t:
        await sequential_main(restful)

    assert t.duration >= 10


@pytest.mark.asyncio
@pytest.mark.parametrize('restful', [False])
async def test_run_async_flow_other_task_concurrent(restful):
    with TimeContext('concurrent await') as t:
        await concurrent_main(restful)

    # some dispatch cost, can't be just 5s, usually at 7~8s, but must <10s
    assert t.duration < 10


@pytest.mark.asyncio
@pytest.mark.parametrize('return_results', [False])
@pytest.mark.parametrize('restful', [False])
async def test_return_results_async_flow(return_results, restful):
    with AsyncFlow(restful=restful, return_results=return_results).add() as f:
        async for r in f.index_ndarray(np.random.random([10, 2])):
            assert isinstance(r, Response)


@pytest.mark.asyncio
@pytest.mark.parametrize('return_results', [False, True])
@pytest.mark.parametrize('restful', [False])
@pytest.mark.parametrize('flow_api', ['delete', 'index', 'update', 'search'])
async def test_return_results_async_flow_crud(return_results, restful, flow_api):
    with AsyncFlow(restful=restful, return_results=return_results).add() as f:
        async for r in getattr(f, flow_api)(documents(0, 10)):
            assert isinstance(r, Response)
