import pytest
import asyncio
import time
import copy
import multiprocessing

from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.peapods.networking import GrpcConnectionPool
from jina.types.message import Message
from jina.types.request import Request
from jina import Document, DocumentArray
from jina.peapods import networking


def test_grpc_gateway_runtime_init_close():
    def create_runtime():
        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--grpc-data-requests',
                    '--graph-description',
                    '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}',
                    '--pods-addresses',
                    '{"pod0": ["0.0.0.0:3246", "0.0.0.0:3247"]}',
                ]
            )
        ) as runtime:
            runtime.run_forever()

    p = multiprocessing.Process(target=create_runtime)
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


def test_grpc_gateway_runtime_handle_messages_linear(linear_graph_dict, monkeypatch):
    monkeypatch.setattr(
        networking,
        'create_connection_pool',
        lambda *args, **kwargs: DummyMockConnectionPool(),
    )
    port_in = 5555  # need to randomize

    def create_runtime():
        import json

        graph_description = json.dumps(linear_graph_dict)
        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-in',
                    '3235',
                    '--graph-description',
                    f'{graph_description}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:
            runtime.run_forever()

    def client_send(client_id: int):
        from jina.clients.request import request_generator

        req = list(
            request_generator(
                '/', DocumentArray([Document(text=f'Request from client{client_id}')])
            )
        )[0]
        msg = Message(None, req, 'test', '123')
        # send message
        response = GrpcConnectionPool.send_message_sync(msg, f'0.0.0.0:{port_in}')
        print(f' response {response}')

    p = multiprocessing.Process(target=create_runtime)
    p.start()
    time.sleep(1.0)
    client_processes = []
    for i in range(10):
        cp = multiprocessing.Process(target=client_send, kwargs={'client_id': i})
        cp.start()
        client_processes.append(cp)
    p.terminate()
    p.join()
    for cp in client_processes:
        cp.terminate()
        cp.join()
