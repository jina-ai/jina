import asyncio
import copy
import multiprocessing
import time
from typing import Dict

import pytest

from jina import Document, DocumentArray
from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.serve import networking
from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.serve.runtimes.gateway.http import HTTPGatewayRuntime
from jina.serve.runtimes.gateway.websocket import WebSocketGatewayRuntime
from jina.types.request.data import DataRequest


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


class DummyNoDocAccessMockConnectionPool:
    def send_requests_once(
        self, requests, deployment: str, head: bool, endpoint: str = None
    ) -> asyncio.Task:
        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            if requests[0].is_decompressed:
                return (
                    DataRequest(request=requests[0].proto.SerializePartialToString()),
                    {},
                )
            else:
                return DataRequest(request=requests[0].buffer), {}

        return asyncio.create_task(task_wrapper())


class DummyMockConnectionPool:
    def send_requests_once(
        self, requests, deployment: str, head: bool, endpoint: str = None
    ) -> asyncio.Task:
        assert head
        request = requests[0]
        response_msg = copy.deepcopy(request)
        new_docs = DocumentArray()
        docs = request.docs
        for doc in docs:
            clientid = doc.text[0:7]
            new_doc = Document(text=doc.text + f'-{clientid}-{deployment}')
            new_docs.append(new_doc)

        response_msg.data.docs = new_docs

        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            return response_msg, {}

        return asyncio.create_task(task_wrapper())


def create_runtime(
    graph_dict: Dict, protocol: str, port: int, call_counts=None, monkeypatch=None
):
    import json

    graph_description = json.dumps(graph_dict)
    runtime_cls = None
    if call_counts:

        def decompress(self):
            call_counts.put_nowait('called')
            from jina.proto import jina_pb2

            self._pb_body = jina_pb2.DataRequestProto()
            self._pb_body.ParseFromString(self.buffer)
            self.buffer = None

        monkeypatch.setattr(
            DataRequest,
            '_decompress',
            decompress,
        )
    if protocol == 'grpc':
        runtime_cls = GRPCGatewayRuntime
    elif protocol == 'http':
        runtime_cls = HTTPGatewayRuntime
    elif protocol == 'websocket':
        runtime_cls = WebSocketGatewayRuntime
    with runtime_cls(
        set_gateway_parser().parse_args(
            [
                '--port',
                f'{port}',
                '--graph-description',
                f'{graph_description}',
                '--deployments-addresses',
                '{}',
            ]
        )
    ) as runtime:
        runtime.run_forever()


def client_send(client_id: int, port: int, protocol: str):
    from jina.clients import Client

    c = Client(protocol=protocol, port=port, return_responses=True)

    # send requests
    return c.post(
        on='/', inputs=DocumentArray([Document(text=f'client{client_id}-Request')])
    )


NUM_PARALLEL_CLIENTS = 10


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_grpc_gateway_runtime_handle_messages_linear(
    linear_graph_dict, monkeypatch, protocol
):
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    port = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-deployment2-client{client_id}-deployment3'
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': linear_graph_dict,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(target=client_validate, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


def test_grpc_gateway_runtime_lazy_request_access(linear_graph_dict, monkeypatch):
    call_counts = multiprocessing.Queue()

    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyNoDocAccessMockConnectionPool.send_requests_once,
    )
    port = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port, 'grpc')
        assert len(responses) > 0

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': 'grpc',
            'port': port,
            'graph_dict': linear_graph_dict,
            'call_counts': call_counts,
            'monkeypatch': monkeypatch,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(target=client_validate, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    assert (
        _queue_length(call_counts) == NUM_PARALLEL_CLIENTS * 2
    )  # request should be decompressed at start and end only
    for cp in client_processes:
        assert cp.exitcode == 0


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_grpc_gateway_runtime_handle_messages_bifurcation(
    bifurcation_graph_dict, monkeypatch, protocol
):
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    port = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port, protocol)
        assert len(responses) > 0
        # reducing is supposed to happen in the deployments, in the test it will get a single doc in non deterministic order
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-deployment3'
            or responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-deployment4-client{client_id}-deployment5'
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': bifurcation_graph_dict,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(target=client_validate, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_grpc_gateway_runtime_handle_messages_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway, monkeypatch, protocol
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    port = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        deployment1_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-merger'
            in responses[0].docs[0].text
        )
        deployment2_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-merger'
            in responses[0].docs[0].text
        )
        assert deployment1_path or deployment2_path

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': merge_graph_dict_directly_merge_in_gateway,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(target=client_validate, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_grpc_gateway_runtime_handle_messages_merge_in_last_deployment(
    merge_graph_dict_directly_merge_in_last_deployment, monkeypatch, protocol
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    port = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        deployment1_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-merger-client{client_id}-deployment_last'
            in responses[0].docs[0].text
        )
        deployment2_path = (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-merger-client{client_id}-deployment_last'
            in responses[0].docs[0].text
        )
        assert deployment1_path or deployment2_path

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': merge_graph_dict_directly_merge_in_last_deployment,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(target=client_validate, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_grpc_gateway_runtime_handle_messages_complete_graph_dict(
    complete_graph_dict, monkeypatch, protocol
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    port = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        # there are 3 incoming paths to merger, it could be any
        assert (
            f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment1-client{client_id}-merger-client{client_id}-deployment_last'
            == responses[0].docs[0].text
            or f'client{client_id}-Request-client{client_id}-deployment0-client{client_id}-deployment2-client{client_id}-deployment3-client{client_id}-merger-client{client_id}-deployment_last'
            == responses[0].docs[0].text
            or f'client{client_id}-Request-client{client_id}-deployment4-client{client_id}-deployment5-client{client_id}-merger-client{client_id}-deployment_last'
            == responses[0].docs[0].text
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port': port,
            'graph_dict': complete_graph_dict,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(target=client_validate, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


def _queue_length(queue: 'multiprocessing.Queue'):
    # Pops elements from the queue and counts them
    # Used if the underlying queue is sensitive to ordering
    # This is used instead of multiprocessing.Queue.qsize() since it is not supported on MacOS
    length = 0
    while not queue.empty():
        queue.get()
        length += 1
    return length
