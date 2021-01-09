import asyncio

import numpy as np
import pytest

from jina.flow.asyncio import AsyncFlow
from jina.types.request import Response
from jina.logging.profile import TimeContext


def validate(req):
    assert len(req.docs) == 5
    assert req.docs[0].blob.ndim == 1


# TODO(Deepankar): with `restful: True` few of the asyncio tests are flaky.
# Though it runs fine locally, results in - `RuntimeError - Event loop closed` in CI (Disabling for now)

@pytest.mark.asyncio
@pytest.mark.parametrize('restful', [False])
async def test_run_async_flow(restful):
    with AsyncFlow(restful=restful).add() as f:
        await f.index_ndarray(np.random.random([5, 4]), on_done=validate)


async def run_async_flow_5s(restful):
    # WaitDriver pause 5s makes total roundtrip ~5s
    with AsyncFlow(restful=restful).add(uses='- !WaitDriver {}') as f:
        await f.index_ndarray(np.random.random([5, 4]), on_done=validate)


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
@pytest.mark.parametrize('return_results', [False, True])
@pytest.mark.parametrize('restful', [False])
async def test_return_results_async_flow(return_results, restful):
    with AsyncFlow(restful=restful, return_results=return_results).add() as f:
        r = await f.index_ndarray(np.random.random([10, 2]))
        if return_results:
            assert isinstance(r, list)
            assert isinstance(r[0], Response)
        else:
            assert r is None
