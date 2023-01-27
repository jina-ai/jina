import pytest

from jina.serve.networking import _ConnectionPoolMap, _NetworkingHistograms


@pytest.mark.asyncio
async def test_head_addition_removal(logger, metrics, port_generator):
    head_port = port_generator()
    head_address = f'0.0.0.0:{head_port}'
    head_deployment = 'head'

    connection_pool = _ConnectionPoolMap(
        runtime_name=head_deployment,
        logger=logger,
        metrics=metrics,
        histograms=_NetworkingHistograms(),
    )
    connection_pool.add_head(
        deployment=head_deployment, address=head_address, head_id=0
    )
    replica_list = connection_pool.get_replicas(deployment=head_deployment, head=True)
    assert replica_list.has_connections()
    assert len(replica_list.get_all_connections()) == 1
    assert not connection_pool.get_replicas(deployment=head_deployment, head=False)

    removed_connection = await connection_pool.remove_head(
        deployment=head_deployment, address=head_address
    )
    assert removed_connection


@pytest.mark.asyncio
async def test_replica_addition_removal(logger, metrics, port_generator):
    connection_pool = _ConnectionPoolMap(
        runtime_name='deployment',
        logger=logger,
        metrics=metrics,
        histograms=_NetworkingHistograms(),
    )

    replica_0_address = f'0.0.0.0:{port_generator()}'
    replica_0_deployment = 'replicas_0'
    connection_pool.add_replica(
        deployment=replica_0_deployment, address=replica_0_address, shard_id=0
    )

    replica_1_address = f'0.0.0.0:{port_generator()}'
    replica_1_deployment = 'replicas_1'
    connection_pool.add_replica(
        deployment=replica_1_deployment, address=replica_1_address, shard_id=0
    )

    assert connection_pool.get_replicas(
        deployment=replica_0_deployment, head=False
    ).has_connections()
    assert connection_pool.get_replicas(
        deployment=replica_1_deployment, head=False
    ).has_connections()

    removed_connection_0 = await connection_pool.remove_replica(
        deployment=replica_0_deployment, address=replica_0_address
    )
    assert removed_connection_0
    removed_connection_1 = await connection_pool.remove_replica(
        deployment=replica_1_deployment, address=replica_1_address
    )
    assert removed_connection_1


def test_independent_shards_and_replicas(logger, metrics, port_generator):
    connection_pool = _ConnectionPoolMap(
        runtime_name='deployment',
        logger=logger,
        metrics=metrics,
        histograms=_NetworkingHistograms(),
    )
    head_port = port_generator()
    head_address = f'0.0.0.0:{head_port}'
    head_deployment = 'head'
    connection_pool.add_head(
        deployment=head_deployment, address=head_address, head_id=0
    )
    assert connection_pool.get_replicas(
        deployment=head_deployment, head=True
    ).has_connections()
    assert not connection_pool.get_replicas_all_shards(deployment=head_deployment)

    replica_0_address = f'0.0.0.0:{port_generator()}'
    replica_0_deployment = 'replicas_0'
    connection_pool.add_replica(
        deployment=replica_0_deployment, address=replica_0_address, shard_id=0
    )

    replica_1_address = f'0.0.0.0:{port_generator()}'
    replica_1_deployment = 'replicas_1'
    connection_pool.add_replica(
        deployment=replica_1_deployment, address=replica_1_address, shard_id=0
    )

    assert connection_pool.get_replicas(
        deployment=replica_0_deployment, head=False
    ).has_connections()
    assert len(connection_pool.get_replicas_all_shards(deployment=replica_0_deployment))
    assert connection_pool.get_replicas(
        deployment=replica_1_deployment, head=False
    ).has_connections()
    assert len(connection_pool.get_replicas_all_shards(deployment=replica_1_deployment))


def test_shards_and_replicas(logger, metrics, port_generator):
    connection_pool = _ConnectionPoolMap(
        runtime_name='deployment',
        logger=logger,
        metrics=metrics,
        histograms=_NetworkingHistograms(),
    )
    head_port = port_generator()
    head_address = f'0.0.0.0:{head_port}'
    head_deployment = 'head'
    connection_pool.add_head(
        deployment=head_deployment, address=head_address, head_id=0
    )
    assert connection_pool.get_replicas(
        deployment=head_deployment, head=True
    ).has_connections()
    assert not connection_pool.get_replicas_all_shards(deployment=head_deployment)

    # create a shard deployment which has 2 replicas
    shard_0_deployment = 'shard_0'
    replica_0_0_address = f'0.0.0.0:{port_generator()}'
    connection_pool.add_replica(
        deployment=shard_0_deployment, address=replica_0_0_address, shard_id=0
    )
    replica_0_1_address = f'0.0.0.0:{port_generator()}'
    connection_pool.add_replica(
        deployment=shard_0_deployment, address=replica_0_1_address, shard_id=1
    )
    assert connection_pool.get_replicas(
        deployment=shard_0_deployment, head=False
    ).has_connections()
    assert (
        len(connection_pool.get_replicas_all_shards(deployment=shard_0_deployment)) == 2
    )

    # create a shard deployment which has 3 replicas
    shard_1_deployment = 'shard_1'
    replica_1_0_address = f'0.0.0.0:{port_generator()}'
    connection_pool.add_replica(
        deployment=shard_1_deployment, address=replica_1_0_address, shard_id=0
    )
    replica_1_1_address = f'0.0.0.0:{port_generator()}'
    connection_pool.add_replica(
        deployment=shard_1_deployment, address=replica_1_1_address, shard_id=1
    )
    replica1_2_address = f'0.0.0.0:{port_generator()}'
    assert connection_pool.get_replicas(
        deployment=shard_1_deployment, head=False
    ).has_connections()
    connection_pool.add_replica(
        deployment=shard_1_deployment, address=replica1_2_address, shard_id=2
    )
    assert (
        len(connection_pool.get_replicas_all_shards(deployment=shard_1_deployment)) == 3
    )
