from dataclasses import dataclass

import pytest

from jina import Document, DocumentArray, Executor, Flow, requests
from jina.serve.networking import _NetworkingHistograms
from jina.serve.networking._connection_stub import ConnectionStubs
from jina.serve.networking.utils import get_grpc_channel
from jina.types.request.data import DataRequest


@dataclass
class DummyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        docs[0].text = 'dummy'


@pytest.mark.asyncio
async def test_init_stubs(metrics, port_generator):
    executor_port = port_generator()
    flow = Flow().add(name='executor0', port=executor_port, uses=DummyExecutor)
    with flow:
        address = f'0.0.0.0:{executor_port}'
        channel = get_grpc_channel(address=address, asyncio=True)
        connection_stub = ConnectionStubs(
            address=address,
            channel=channel,
            deployment_name='executor0',
            metrics=metrics,
            histograms=_NetworkingHistograms(),
        )
        assert not connection_stub._initialized
        await connection_stub._init_stubs()
        assert connection_stub._initialized


@pytest.mark.asyncio
async def test_send_discover_endpoint(metrics, port_generator):
    executor_port = port_generator()
    flow = Flow().add(name='executor0', port=executor_port, uses=DummyExecutor)
    with flow:
        address = f'0.0.0.0:{executor_port}'
        channel = get_grpc_channel(address=address, asyncio=True)
        connection_stub = ConnectionStubs(
            address='executor0',
            channel=channel,
            deployment_name='executor-0',
            metrics=metrics,
            histograms=_NetworkingHistograms(),
        )

        response, _ = await connection_stub.send_discover_endpoint()
        assert set(response.endpoints) == {'/default', '_jina_dry_run_'}


@pytest.mark.asyncio
async def test_send_info_rpc(metrics, port_generator):
    executor_port = port_generator()
    flow = Flow().add(name='executor0', port=executor_port, uses=DummyExecutor)
    with flow:
        address = f'0.0.0.0:{executor_port}'
        channel = get_grpc_channel(address=address, asyncio=True)
        connection_stub = ConnectionStubs(
            address='executor0',
            channel=channel,
            deployment_name='executor-0',
            metrics=metrics,
            histograms=_NetworkingHistograms(),
        )

        response = await connection_stub.send_info_rpc()
        assert response.jina
        assert response.envs


@pytest.mark.asyncio
async def test_send_requests(metrics, port_generator):
    executor_port = port_generator()
    flow = Flow().add(name='executor0', port=executor_port, uses=DummyExecutor)
    with flow:
        address = f'0.0.0.0:{executor_port}'
        channel = get_grpc_channel(address=address, asyncio=True)
        connection_stub = ConnectionStubs(
            address='executor0',
            channel=channel,
            deployment_name='executor-0',
            metrics=metrics,
            histograms=_NetworkingHistograms(),
        )

        request = DataRequest()
        request.data.docs = DocumentArray(Document())
        response, _ = await connection_stub.send_requests(
            requests=[request], metadata={}, compression=False
        )
        assert response.data.docs[0].text == 'dummy'
