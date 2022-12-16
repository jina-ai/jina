import asyncio
import copy
import json
import multiprocessing
import time
from multiprocessing import Process

import grpc
import pytest

from docarray import Document, DocumentArray
from jina.clients.request import request_generator
from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.serve import networking
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime


def test_grpc_gateway_runtime_init_close():
    deployment0_port = random_port()
    deployment1_port = random_port()
    port = random_port()

    def _create_runtime():
        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    str(port),
                    '--graph-description',
                    '{"start-gateway": ["deployment0"], "deployment0": ["end-gateway"]}',
                    '--deployments-addresses',
                    '{"deployment0": ["0.0.0.0:'
                    + f'{deployment0_port}'
                    + '", "0.0.0.0:'
                    + f'{deployment1_port}'
                    + '"]}',
                ]
            )
        ) as runtime:
            runtime.run_forever()

    p = multiprocessing.Process(target=_create_runtime)
    p.start()
    time.sleep(1.0)
    assert AsyncNewLoopRuntime.is_ready(ctrl_address=f'127.0.0.1:{port}')
    p.terminate()
    p.join()

    assert p.exitcode == 0


@pytest.fixture
def linear_graph_dict():
    return {
        'start-gateway': ['deployment0'],
        'deployment0': ['deployment1'],
        'deployment1': ['deployment2'],
        'deployment2': ['deployment3'],
        'deployment3': ['end-gateway'],
    }


@pytest.fixture
def bifurcation_graph_dict():
    return {
        'start-gateway': ['deployment0', 'deployment4', 'deployment6'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': [],  # hanging_deployment
        'deployment2': ['deployment3'],
        'deployment4': ['deployment5'],
        'deployment5': ['end-gateway'],
        'deployment3': ['deployment5'],
        'deployment6': [],  # hanging_deployment
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_gateway():
    return {
        'start-gateway': ['deployment0'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['merger'],
        'deployment2': ['merger'],
        'merger': ['end-gateway'],
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_last_deployment():
    return {
        'start-gateway': ['deployment0'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['merger'],
        'deployment2': ['merger'],
        'merger': ['deployment_last'],
        'deployment_last': ['end-gateway'],
    }


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['deployment0', 'deployment4', 'deployment6'],
        'deployment0': ['deployment1', 'deployment2'],
        'deployment1': ['merger'],
        'deployment2': ['deployment3'],
        'deployment4': ['deployment5'],
        'merger': ['deployment_last'],
        'deployment5': ['merger'],
        'deployment3': ['merger'],
        'deployment6': [],  # hanging_deployment
        'deployment_last': ['end-gateway'],
    }


class DummyMockConnectionPool:
    def send_requests_once(
        self,
        requests,
        deployment: str,
        head: bool,
        metadata: dict = None,
        shard_id=None,
        endpoint: str = None,
        timeout: float = 1.0,
        retries: int = -1,
    ) -> asyncio.Task:
        assert head
        response_msg = copy.deepcopy(requests[0])
        new_docs = DocumentArray()
        for doc in requests[0].docs:
            clientid = doc.text[0:7]
            new_doc = Document(id=doc.id, text=doc.text + f'-{clientid}-{deployment}')
            new_docs.append(new_doc)

        response_msg.data.docs = new_docs

        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            return response_msg, {}

        return asyncio.create_task(task_wrapper())

    def send_discover_endpoint(self, *args, **kwargs):
        async def task_wrapper():
            from jina import __default_endpoint__
            from jina.proto import jina_pb2

            ep = jina_pb2.EndpointsProto()
            ep.endpoints.extend([__default_endpoint__])
            return ep, None

        return asyncio.create_task(task_wrapper())


async def _test(streamer, stream):
    responses = []
    req = request_generator('/', DocumentArray([Document(text='client0-Request')]))
    if stream:
        async for resp in streamer.stream(request_iterator=req):
            responses.append(resp)
    else:
        for req in request_generator(
            '/',
            DocumentArray([Document(text='client0-Request')]),
        ):
            unary_response = await streamer.process_single_data(request=req)
            responses.append(unary_response)
    return responses


@pytest.mark.parametrize('stream', [True, False])
def test_grpc_gateway_runtime_handle_messages_linear(
    linear_graph_dict, monkeypatch, stream
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_discover_endpoint',
            DummyMockConnectionPool.send_discover_endpoint,
        )
        port = random_port()

        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    f'{port}',
                    '--graph-description',
                    f'{json.dumps(linear_graph_dict)}',
                    '--deployments-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            responses = asyncio.run(_test(runtime.gateway.streamer, stream))

        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client0-Request-client0-deployment0-client0-deployment1-client0-deployment2-client0-deployment3'
        )

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


@pytest.mark.parametrize('stream', [True, False])
def test_grpc_gateway_runtime_handle_messages_bifurcation(
    bifurcation_graph_dict, monkeypatch, stream
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_discover_endpoint',
            DummyMockConnectionPool.send_discover_endpoint,
        )
        port = random_port()

        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    f'{port}',
                    '--graph-description',
                    f'{json.dumps(bifurcation_graph_dict)}',
                    '--deployments-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            responses = asyncio.run(_test(runtime.gateway.streamer, stream))

        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client0-Request-client0-deployment0-client0-deployment2-client0-deployment3'
            or responses[0].docs[0].text
            == f'client0-Request-client0-deployment4-client0-deployment5'
        )

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


@pytest.mark.parametrize('stream', [True, False])
def test_grpc_gateway_runtime_handle_messages_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway, monkeypatch, stream
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_discover_endpoint',
            DummyMockConnectionPool.send_discover_endpoint,
        )
        port = random_port()

        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    f'{port}',
                    '--graph-description',
                    f'{json.dumps(merge_graph_dict_directly_merge_in_gateway)}',
                    '--deployments-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            responses = asyncio.run(_test(runtime.gateway.streamer, stream))

        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        deployment1_path = (
            f'client0-Request-client0-deployment0-client0-deployment1-client0-merger'
            in responses[0].docs[0].text
        )
        deployment2_path = (
            f'client0-Request-client0-deployment0-client0-deployment2-client0-merger'
            in responses[0].docs[0].text
        )
        assert deployment1_path or deployment2_path

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


@pytest.mark.parametrize('stream', [True, False])
def test_grpc_gateway_runtime_handle_messages_merge_in_last_deployment(
    merge_graph_dict_directly_merge_in_last_deployment, monkeypatch, stream
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_discover_endpoint',
            DummyMockConnectionPool.send_discover_endpoint,
        )
        port = random_port()

        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    f'{port}',
                    '--graph-description',
                    f'{json.dumps(merge_graph_dict_directly_merge_in_last_deployment)}',
                    '--deployments-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            responses = asyncio.run(_test(runtime.gateway.streamer, stream))

        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        deployment1_path = (
            f'client0-Request-client0-deployment0-client0-deployment1-client0-merger-client0-deployment_last'
            in responses[0].docs[0].text
        )
        deployment2_path = (
            f'client0-Request-client0-deployment0-client0-deployment2-client0-merger-client0-deployment_last'
            in responses[0].docs[0].text
        )
        assert deployment1_path or deployment2_path

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


@pytest.mark.parametrize('stream', [True, False])
def test_grpc_gateway_runtime_handle_messages_complete_graph_dict(
    complete_graph_dict, monkeypatch, stream
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_discover_endpoint',
            DummyMockConnectionPool.send_discover_endpoint,
        )
        port = random_port()

        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    f'{port}',
                    '--graph-description',
                    f'{json.dumps(complete_graph_dict)}',
                    '--deployments-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            responses = asyncio.run(_test(runtime.gateway.streamer, stream))

        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        deployment2_path = (
            f'client0-Request-client0-deployment0-client0-deployment2-client0-deployment3-client0-merger-client0-deployment_last'
            == responses[0].docs[0].text
        )
        deployment4_path = (
            f'client0-Request-client0-deployment4-client0-deployment5-client0-merger-client0-deployment_last'
            == responses[0].docs[0].text
        )
        assert (
            f'client0-Request-client0-deployment0-client0-deployment1-client0-merger-client0-deployment_last'
            == responses[0].docs[0].text
            or deployment2_path
            or deployment4_path
        )

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


@pytest.mark.parametrize('stream', [True, False])
def test_grpc_gateway_runtime_handle_empty_graph(stream):
    def process_wrapper():
        port = random_port()

        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    f'{port}',
                    '--graph-description',
                    f'{json.dumps({})}',
                    '--deployments-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            responses = asyncio.run(_test(runtime.gateway.streamer, stream))

        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert responses[0].docs[0].text == f'client0-Request'

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


@pytest.mark.asyncio
async def test_grpc_gateway_runtime_reflection():
    deployment0_port = random_port()
    deployment1_port = random_port()
    port = random_port()

    def _create_runtime():
        with GatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    str(port),
                    '--graph-description',
                    '{"start-gateway": ["deployment0"], "deployment0": ["end-gateway"]}',
                    '--deployments-addresses',
                    '{"deployment0": ["0.0.0.0:'
                    + f'{deployment0_port}'
                    + '", "0.0.0.0:'
                    + f'{deployment1_port}'
                    + '"]}',
                ]
            )
        ) as runtime:
            runtime.run_forever()

    p = multiprocessing.Process(target=_create_runtime)
    p.start()
    time.sleep(1.0)
    assert AsyncNewLoopRuntime.is_ready(ctrl_address=f'127.0.0.1:{port}')

    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        service_names = await GrpcConnectionPool.get_available_services(channel)

    assert all(
        service_name in service_names
        for service_name in [
            'jina.JinaInfoRPC',
            'jina.JinaRPC',
            'jina.JinaSingleDataRequestRPC',
        ]
    )

    p.terminate()
    p.join()

    assert p.exitcode == 0
