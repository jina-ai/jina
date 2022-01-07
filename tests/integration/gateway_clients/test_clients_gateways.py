import asyncio
import copy
import multiprocessing
import time
from typing import Dict

import pytest

from jina import Document, DocumentArray
from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.peapods import networking
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.peapods.runtimes.gateway.http import HTTPGatewayRuntime
from jina.peapods.runtimes.gateway.websocket import WebSocketGatewayRuntime
from jina.types.request.data import DataRequest


@pytest.fixture
def linear_graph_dict():
    return {
        'start-gateway': ['pod0'],
        'pod0': ['pod1'],
        'pod1': ['pod2'],
        'pod2': ['pod3'],
        'pod3': ['end-gateway'],
    }


@pytest.fixture
def bifurcation_graph_dict():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6'],
        'pod0': ['pod1', 'pod2'],
        'pod1': [],  # hanging_pod
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'pod5': ['end-gateway'],
        'pod3': ['pod5'],
        'pod6': [],  # hanging_pod
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_gateway():
    return {
        'start-gateway': ['pod0'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['merger'],
        'merger': ['end-gateway'],
    }


@pytest.fixture
def merge_graph_dict_directly_merge_in_last_pod():
    return {
        'start-gateway': ['pod0'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['merger'],
        'merger': ['pod_last'],
        'pod_last': ['end-gateway'],
    }


@pytest.fixture
def complete_graph_dict():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6'],
        'pod0': ['pod1', 'pod2'],
        'pod1': ['merger'],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'merger': ['pod_last'],
        'pod5': ['merger'],
        'pod3': ['merger'],
        'pod6': [],  # hanging_pod
        'pod_last': ['end-gateway'],
    }


class DummyNoDocAccessMockConnectionPool:
    def send_requests_once(
        self, requests, pod: str, head: bool, endpoint: str = None
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
        self, requests, pod: str, head: bool, endpoint: str = None
    ) -> asyncio.Task:
        assert head
        request = requests[0]
        response_msg = copy.deepcopy(request)
        new_docs = DocumentArray()
        for doc in request.docs:
            clientid = doc.text[0:7]
            new_doc = Document(text=doc.text + f'-{clientid}-{pod}')
            new_docs.append(new_doc)

        response_msg.docs.clear()
        response_msg.docs.extend(new_docs)

        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            return response_msg, {}

        return asyncio.create_task(task_wrapper())


def create_runtime(
    graph_dict: Dict, protocol: str, port_in: int, call_counts=None, monkeypatch=None
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
                '--port-expose',
                f'{port_in}',
                '--graph-description',
                f'{graph_description}',
                '--pods-addresses',
                '{}',
            ]
        )
    ) as runtime:
        runtime.run_forever()


def client_send(client_id: int, port_in: int, protocol: str):
    from jina.clients import Client

    c = Client(protocol=protocol, port=port_in)

    # send requests
    return c.post(
        on='/',
        inputs=DocumentArray([Document(text=f'client{client_id}-Request')]),
        return_results=True,
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
    port_in = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port_in, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-pod2-client{client_id}-pod3'
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port_in': port_in,
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
    port_in = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port_in, 'grpc')
        assert len(responses) > 0

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': 'grpc',
            'port_in': port_in,
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
        call_counts.qsize() == NUM_PARALLEL_CLIENTS * 2
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
    port_in = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port_in, protocol)
        assert len(responses) > 0
        # reducing is supposed to happen in the pods, in the test it will get a single doc in non deterministic order
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3'
            or responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5'
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port_in': port_in,
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
    port_in = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port_in, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        pod1_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger'
            in responses[0].docs[0].text
        )
        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-merger'
            in responses[0].docs[0].text
        )
        assert pod1_path or pod2_path

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port_in': port_in,
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
def test_grpc_gateway_runtime_handle_messages_merge_in_last_pod(
    merge_graph_dict_directly_merge_in_last_pod, monkeypatch, protocol
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_requests_once',
        DummyMockConnectionPool.send_requests_once,
    )
    port_in = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port_in, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        pod1_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger-client{client_id}-pod_last'
            in responses[0].docs[0].text
        )
        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-merger-client{client_id}-pod_last'
            in responses[0].docs[0].text
        )
        assert pod1_path or pod2_path

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port_in': port_in,
            'graph_dict': merge_graph_dict_directly_merge_in_last_pod,
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
    port_in = random_port()

    def client_validate(client_id: int):
        responses = client_send(client_id, port_in, protocol)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        # there are 3 incoming paths to merger, it could be any
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-merger-client{client_id}-pod_last'
            == responses[0].docs[0].text
            or f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3-client{client_id}-merger-client{client_id}-pod_last'
            == responses[0].docs[0].text
            or f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5-client{client_id}-merger-client{client_id}-pod_last'
            == responses[0].docs[0].text
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={
            'protocol': protocol,
            'port_in': port_in,
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
