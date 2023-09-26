import pytest

from jina import Flow


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_dry_run(protocol):
    f = Flow(protocols=protocol).add()
    with f:
        dry_run = f.is_flow_ready()
    dry_run_negative = f.is_flow_ready()

    assert dry_run
    assert not dry_run_negative


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('show_table', [True, False])
def test_profiling(protocol, show_table):
    f = Flow(protocol=protocol).add(name='hello').add(name='world')
    with f:
        results = f.profiling(show_table=show_table)
    assert results
    assert 'hello' in results
    assert 'world' in results


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc'])
async def test_profiling_async(protocol):
    f = Flow(protocol=protocol, asyncio=True).add(name='hello').add(name='world')
    with f:
        results = await f.profiling()
    assert results
    assert 'hello' in results
    assert 'world' in results
