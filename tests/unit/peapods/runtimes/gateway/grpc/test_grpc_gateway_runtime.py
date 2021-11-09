import pytest
import asyncio
import time
import copy
import multiprocessing

from typing import Dict

from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.types.message import Message
from jina.types.request import Request
from jina import Document, DocumentArray
from jina.peapods import networking
from jina.helper import random_port


def test_grpc_gateway_runtime_init_close():
    pod0_port = random_port()
    pod1_port = random_port()

    def _create_runtime():
        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--grpc-data-requests',
                    '--graph-description',
                    '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
                    '--pods-addresses',
                    '{"pod0": ["0.0.0.0:'
                    + f'{pod0_port}'
                    + '", "0.0.0.0:'
                    + f'{pod1_port}'
                    + '"]}',
                ]
            )
        ) as runtime:
            runtime.run_forever()

    p = multiprocessing.Process(target=_create_runtime)
    p.start()
    time.sleep(1.0)
    p.terminate()
    p.join()

    assert p.exitcode == 0


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
        'pod3': ['end-gateway'],
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
        'pod1': ['end-gateway'],
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'merger': ['pod_last'],
        'pod5': ['merger'],
        'pod3': ['merger'],
        'pod6': [],  # hanging_pod
        'pod_last': ['end-gateway'],
    }


@pytest.fixture
def graph_hanging_pod_after_merge():
    return {
        'start-gateway': ['pod0', 'pod4', 'pod6', 'pod8'],
        'pod0': ['pod1', 'pod2'],
        'pod1': [],  # hanging_pod
        'pod2': ['pod3'],
        'pod4': ['pod5'],
        'pod5': ['end-gateway'],
        'pod3': ['end-gateway'],
        'pod6': ['pod7'],
        'pod8': ['pod7'],
        'pod7': ['pod9'],
        'pod9': [],  # hanging_pod
    }


class DummyMockConnectionPool:
    def send_message(self, msg: Message, pod: str, head: bool) -> asyncio.Task:
        assert head
        response_msg = copy.deepcopy(msg)
        response_msg.request = Request(msg.request.proto, copy=True)
        request = msg.request
        new_docs = DocumentArray()
        for doc in request.docs:
            clientid = doc.text[0:7]
            new_doc = Document(text=doc.text + f'-{clientid}-{pod}')
            new_docs.append(new_doc)

        response_msg.request.docs.clear()
        response_msg.request.docs.extend(new_docs)

        async def task_wrapper():
            import random

            await asyncio.sleep(1 / (random.randint(1, 3) * 10))
            return response_msg

        return asyncio.create_task(task_wrapper())


def create_runtime(graph_dict: Dict, port_in: int):
    import json

    graph_description = json.dumps(graph_dict)
    with GRPCGatewayRuntime(
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


def client_send(client_id: int, port_in: int):
    from jina.clients import Client

    c = Client(protocol='grpc', port=port_in)

    # send requests
    return c.post(
        on='/',
        inputs=DocumentArray([Document(text=f'client{client_id}-Request')]),
        return_results=True,
    )


NUM_PARALLEL_CLIENTS = 10


def test_grpc_gateway_runtime_handle_messages_linear(linear_graph_dict, monkeypatch):
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_message',
        DummyMockConnectionPool.send_message,
    )
    port_in = random_port()

    def client_validate(client_id: int, port_in: int):
        responses = client_send(client_id, port_in)
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1-client{client_id}-pod2-client{client_id}-pod3'
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={'port_in': port_in, 'graph_dict': linear_graph_dict},
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(
            target=client_validate, kwargs={'client_id': i, 'port_in': port_in}
        )
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_bifurcation(
    bifurcation_graph_dict, monkeypatch
):
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_message',
        DummyMockConnectionPool.send_message,
    )
    port_in = random_port()

    def client_validate(client_id: int, port_in: int):
        responses = client_send(client_id, port_in)
        assert len(responses) > 0
        assert len(responses[0].docs) == 2
        assert (
            responses[0].docs[0].text
            == f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3'
        )
        assert (
            responses[0].docs[1].text
            == f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5'
        )

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={'port_in': port_in, 'graph_dict': bifurcation_graph_dict},
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(
            target=client_validate, kwargs={'client_id': i, 'port_in': port_in}
        )
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway, monkeypatch
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_message',
        DummyMockConnectionPool.send_message,
    )
    port_in = random_port()

    def client_validate(client_id: int, port_in: int):
        responses = client_send(client_id, port_in)
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
            'port_in': port_in,
            'graph_dict': merge_graph_dict_directly_merge_in_gateway,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(
            target=client_validate, kwargs={'client_id': i, 'port_in': port_in}
        )
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_merge_in_last_pod(
    merge_graph_dict_directly_merge_in_last_pod, monkeypatch
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_message',
        DummyMockConnectionPool.send_message,
    )
    port_in = random_port()

    def client_validate(client_id: int, port_in: int):
        responses = client_send(client_id, port_in)
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
            'port_in': port_in,
            'graph_dict': merge_graph_dict_directly_merge_in_last_pod,
        },
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(
            target=client_validate, kwargs={'client_id': i, 'port_in': port_in}
        )
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_complete_graph_dict(
    complete_graph_dict, monkeypatch
):
    # TODO: Test incomplete until merging of responses is ready
    monkeypatch.setattr(
        networking.GrpcConnectionPool,
        'send_message',
        DummyMockConnectionPool.send_message,
    )
    port_in = random_port()

    def client_validate(client_id: int, port_in: int):
        responses = client_send(client_id, port_in)
        assert len(responses) > 0
        assert len(responses[0].docs) == 2
        assert (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod1'
            == responses[0].docs[0].text
        )

        pod2_path = (
            f'client{client_id}-Request-client{client_id}-pod0-client{client_id}-pod2-client{client_id}-pod3-client{client_id}-merger-client{client_id}-pod_last'
            == responses[0].docs[1].text
        )
        pod4_path = (
            f'client{client_id}-Request-client{client_id}-pod4-client{client_id}-pod5-client{client_id}-merger-client{client_id}-pod_last'
            == responses[0].docs[1].text
        )

        assert pod2_path or pod4_path

    p = multiprocessing.Process(
        target=create_runtime,
        kwargs={'port_in': port_in, 'graph_dict': complete_graph_dict},
    )
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(NUM_PARALLEL_CLIENTS):
        cp = multiprocessing.Process(
            target=client_validate, kwargs={'client_id': i, 'port_in': port_in}
        )
        cp.start()
        client_processes.append(cp)

    for cp in client_processes:
        cp.join()
    p.terminate()
    p.join()
    for cp in client_processes:
        assert cp.exitcode == 0
