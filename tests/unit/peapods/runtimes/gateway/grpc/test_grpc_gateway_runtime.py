import asyncio
import copy
import json
import multiprocessing
import time
from multiprocessing import Process

import pytest

from jina import Document, DocumentArray
from jina.clients.request import request_generator
from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.peapods import networking
from jina.peapods.runtimes.asyncio import AsyncNewLoopRuntime
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.types.request.data import DataRequest


def test_grpc_gateway_runtime_init_close():
    pod0_port = random_port()
    pod1_port = random_port()
    port_expose = random_port()

    def _create_runtime():
        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    str(port_expose),
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
    assert AsyncNewLoopRuntime.is_ready(ctrl_address=f'127.0.0.1:{port_expose}')
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


class DummyMockConnectionPool:
    def send_requests_once(
        self, requests, pod: str, head: bool, endpoint: str = None
    ) -> asyncio.Task:
        assert head
        response_msg = copy.deepcopy(requests[0])
        new_docs = DocumentArray()
        for doc in requests[0].docs:
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


def test_grpc_gateway_runtime_handle_messages_linear(linear_graph_dict, monkeypatch):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        port_in = random_port()

        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    f'{port_in}',
                    '--graph-description',
                    f'{json.dumps(linear_graph_dict)}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:

            async def _test():
                responses = []
                req = request_generator(
                    '/', DocumentArray([Document(text='client0-Request')])
                )
                async for resp in runtime.streamer.Call(request_iterator=req):
                    responses.append(resp)
                return responses

            responses = asyncio.run(_test())
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client0-Request-client0-pod0-client0-pod1-client0-pod2-client0-pod3'
        )

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_bifurcation(
    bifurcation_graph_dict, monkeypatch
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        port_in = random_port()

        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    f'{port_in}',
                    '--graph-description',
                    f'{json.dumps(bifurcation_graph_dict)}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:

            async def _test():
                responses = []
                req = request_generator(
                    '/', DocumentArray([Document(text='client0-Request')])
                )
                async for resp in runtime.streamer.Call(request_iterator=req):
                    responses.append(resp)
                return responses

            responses = asyncio.run(_test())
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert (
            responses[0].docs[0].text
            == f'client0-Request-client0-pod0-client0-pod2-client0-pod3'
            or responses[0].docs[0].text == f'client0-Request-client0-pod4-client0-pod5'
        )

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_merge_in_gateway(
    merge_graph_dict_directly_merge_in_gateway, monkeypatch
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        port_in = random_port()

        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    f'{port_in}',
                    '--graph-description',
                    f'{json.dumps(merge_graph_dict_directly_merge_in_gateway)}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:

            async def _test():
                responses = []
                req = request_generator(
                    '/', DocumentArray([Document(text='client0-Request')])
                )
                async for resp in runtime.streamer.Call(request_iterator=req):
                    responses.append(resp)
                return responses

            responses = asyncio.run(_test())
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        pod1_path = (
            f'client0-Request-client0-pod0-client0-pod1-client0-merger'
            in responses[0].docs[0].text
        )
        pod2_path = (
            f'client0-Request-client0-pod0-client0-pod2-client0-merger'
            in responses[0].docs[0].text
        )
        assert pod1_path or pod2_path

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_merge_in_last_pod(
    merge_graph_dict_directly_merge_in_last_pod, monkeypatch
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        port_in = random_port()

        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    f'{port_in}',
                    '--graph-description',
                    f'{json.dumps(merge_graph_dict_directly_merge_in_last_pod)}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:

            async def _test():
                responses = []
                req = request_generator(
                    '/', DocumentArray([Document(text='client0-Request')])
                )
                async for resp in runtime.streamer.Call(request_iterator=req):
                    responses.append(resp)
                return responses

            responses = asyncio.run(_test())
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        pod1_path = (
            f'client0-Request-client0-pod0-client0-pod1-client0-merger-client0-pod_last'
            in responses[0].docs[0].text
        )
        pod2_path = (
            f'client0-Request-client0-pod0-client0-pod2-client0-merger-client0-pod_last'
            in responses[0].docs[0].text
        )
        assert pod1_path or pod2_path

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_grpc_gateway_runtime_handle_messages_complete_graph_dict(
    complete_graph_dict, monkeypatch
):
    def process_wrapper():
        monkeypatch.setattr(
            networking.GrpcConnectionPool,
            'send_requests_once',
            DummyMockConnectionPool.send_requests_once,
        )
        port_in = random_port()

        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    f'{port_in}',
                    '--graph-description',
                    f'{json.dumps(complete_graph_dict)}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:

            async def _test():
                responses = []
                req = request_generator(
                    '/', DocumentArray([Document(text='client0-Request')])
                )
                async for resp in runtime.streamer.Call(request_iterator=req):
                    responses.append(resp)
                return responses

            responses = asyncio.run(_test())
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        pod2_path = (
            f'client0-Request-client0-pod0-client0-pod2-client0-pod3-client0-merger-client0-pod_last'
            == responses[0].docs[0].text
        )
        pod4_path = (
            f'client0-Request-client0-pod4-client0-pod5-client0-merger-client0-pod_last'
            == responses[0].docs[0].text
        )
        assert (
            f'client0-Request-client0-pod0-client0-pod1-client0-merger-client0-pod_last'
            == responses[0].docs[0].text
            or pod2_path
            or pod4_path
        )

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_grpc_gateway_runtime_handle_empty_graph():
    def process_wrapper():
        port_in = random_port()

        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port-expose',
                    f'{port_in}',
                    '--graph-description',
                    f'{json.dumps({})}',
                    '--pods-addresses',
                    '{}',
                ]
            )
        ) as runtime:

            async def _test():
                responses = []
                req = request_generator(
                    '/', DocumentArray([Document(text='client0-Request')])
                )
                async for resp in runtime.streamer.Call(request_iterator=req):
                    responses.append(resp)
                return responses

            responses = asyncio.run(_test())
        assert len(responses) > 0
        assert len(responses[0].docs) == 1
        assert responses[0].docs[0].text == f'client0-Request'

    p = Process(target=process_wrapper)
    p.start()
    p.join()
    assert p.exitcode == 0
