import asyncio

import pytest
from grpc import ChannelConnectivity

from jina.serve.networking.connection_stub import _ConnectionStubs
from jina.serve.networking.instrumentation import _NetworkingHistograms
from jina.serve.networking.replica_list import _ReplicaList


@pytest.fixture()
def replica_list(logger, metrics):
    return _ReplicaList(
        metrics=metrics,
        histograms=_NetworkingHistograms(),
        logger=logger,
        runtime_name='test',
    )


def test_add_connection(replica_list):
    replica_list.add_connection('executor0', 'executor-0')
    assert replica_list.has_connections()
    assert replica_list.has_connection('executor0')
    assert len(replica_list.warmup_stubs)
    assert not replica_list.has_connection('random-address')
    assert len(replica_list.get_all_connections()) == 1


@pytest.mark.asyncio
async def test_remove_connection(replica_list):
    replica_list.add_connection('executor0', 'executor-0')
    assert replica_list.has_connections()
    await replica_list.remove_connection('executor0')
    assert not replica_list.has_connections()
    assert not replica_list.has_connection('executor0')
    # warmup stubs are not updated in the remove_connection method
    assert len(replica_list.warmup_stubs)
    # unknown/unmanaged connections
    removed_connection_invalid = await replica_list.remove_connection('random-address')
    assert removed_connection_invalid is None
    assert len(replica_list.get_all_connections()) == 0


@pytest.mark.asyncio
async def test_reset_connection(replica_list):
    replica_list.add_connection('executor0', 'executor-0')
    connection_stub = await replica_list.get_next_connection('executor0')
    await replica_list.reset_connection('executor0', 'executor-0')
    new_connection_stub = await replica_list.get_next_connection()
    assert len(replica_list.get_all_connections()) == 1

    connection_stub_random_address = await replica_list.reset_connection(
        'random-address', '0'
    )
    assert connection_stub_random_address is None


@pytest.mark.asyncio
async def test_close(replica_list):
    replica_list.add_connection('executor0', 'executor-0')
    replica_list.add_connection('executor1', 'executor-0')
    assert replica_list.has_connection('executor0')
    assert replica_list.has_connection('executor1')
    await replica_list.close()
    assert not replica_list.has_connections()
    assert not len(replica_list.warmup_stubs)


async def _print_channel_attributes(connection_stub: _ConnectionStubs):
    await asyncio.sleep(0.5)
    assert connection_stub.channel.get_state() != ChannelConnectivity.SHUTDOWN


@pytest.mark.asyncio
async def test_synchornization_when_resetting_connection(replica_list, logger):
    replica_list.add_connection('executor0', 'executor-0')
    connection_stub = await replica_list.get_next_connection(num_retries=0)
    responses = await asyncio.gather(
        asyncio.create_task(_print_channel_attributes(connection_stub)),
        asyncio.create_task(
            replica_list.reset_connection(
                address='executor0', deployment_name='executor-0'
            )
        ),
        return_exceptions=True,
    )
    assert not any(
        [issubclass(type(response), BaseException) for response in responses]
    )
