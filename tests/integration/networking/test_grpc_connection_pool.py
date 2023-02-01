import asyncio

import mock
import pytest

from jina import Document, DocumentArray, Flow
from jina.serve.networking import GrpcConnectionPool
from jina.types.request.data import DataRequest
from tests.integration.networking import DummyExecutor


@pytest.fixture
def mocked_connection_pool_map(mocker):
    mock_connection_pool_map = mock.AsyncMock()
    mocker.patch(
        'jina.serve.networking._ConnectionPoolMap',
        return_value=mock_connection_pool_map,
    )
    return mock_connection_pool_map


@pytest.mark.asyncio
async def test_add_remove_connection(logger, mocked_connection_pool_map):
    connection_pool = GrpcConnectionPool(runtime_name='gateway')
    connection_pool.add_connection(deployment='head', address='head', head=True)
    connection_pool.add_connection(deployment='executor0', address='executor0')
    assert mocked_connection_pool_map.add_head.called
    assert mocked_connection_pool_map.add_replica.called
    assert len(connection_pool._deployment_address_map) == 2

    await connection_pool.remove_connection(
        deployment='head', address='head', head=True
    )
    await connection_pool.remove_connection(deployment='executor0', address='executor0')
    assert mocked_connection_pool_map.remove_head.called
    assert mocked_connection_pool_map.remove_replica.called
    # underlying connection pool is destroyed but the deployment -> _ConnectionPoolMap is preserved
    assert len(connection_pool._deployment_address_map) == 2


@pytest.mark.asyncio
async def test_send_discover_endpoint(logger, port_generator):
    connection_pool = GrpcConnectionPool(runtime_name='gateway')
    head_port = port_generator()
    head_address = f'0.0.0.0:{head_port}'
    head_deployment = 'head'

    executor_port = port_generator()
    executor_address = f'0.0.0.0:{executor_port}'
    executor_deployment = 'executor0'

    flow = (
        Flow()
        .add(name=head_deployment, port=head_port, shards=2, uses=DummyExecutor)
        .add(name=executor_deployment, port=executor_port, uses=DummyExecutor)
    )
    with flow:
        connection_pool.add_connection(
            deployment=head_deployment, address=head_address, head=True
        )
        response, _ = await connection_pool.send_discover_endpoint(
            deployment=head_deployment, head=True
        )
        assert set(response.endpoints) == {'/default', '_jina_dry_run_'}

        connection_pool.add_connection(
            deployment=executor_deployment, address=executor_address, head=False
        )
        response, _ = await connection_pool.send_discover_endpoint(
            deployment=executor_deployment, head=False
        )
        assert set(response.endpoints) == {'/default', '_jina_dry_run_'}


@pytest.mark.asyncio
async def test_send_requests_once(logger, port_generator):
    connection_pool = GrpcConnectionPool(runtime_name='gateway')
    executor_port = port_generator()
    executor_address = f'0.0.0.0:{executor_port}'
    executor_deployment = 'executor0'

    flow = Flow().add(name=executor_deployment, port=executor_port, uses=DummyExecutor)
    with flow:
        connection_pool.add_connection(
            deployment=executor_deployment, address=executor_address, head=False
        )
        request = DataRequest()
        request.data.docs = DocumentArray(Document())
        response, _ = await connection_pool.send_requests_once(
            requests=[request], deployment=executor_deployment
        )
        assert response.data.docs[0].text == 'dummy'


@pytest.mark.asyncio
async def test_send_requests(logger, port_generator):
    connection_pool = GrpcConnectionPool(runtime_name='gateway')
    executor_port = port_generator()
    executor_address = f'0.0.0.0:{executor_port}'
    executor_deployment = 'executor0'

    flow = Flow().add(name=executor_deployment, port=executor_port, uses=DummyExecutor)
    with flow:
        connection_pool.add_connection(
            deployment=executor_deployment, address=executor_address, head=False
        )
        request = DataRequest()
        request.data.docs = DocumentArray(Document())
        responses = await asyncio.gather(
            *connection_pool.send_requests(
                requests=[request], deployment=executor_deployment
            ),
            return_exceptions=True,
        )
        assert len(responses) == 1
        response, _ = responses[0]  # unpack tuple of (DataRequest, Metadata)
        assert response.data.docs[0].text == 'dummy'
        assert response.header.exec_endpoint == ''
