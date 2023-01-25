import asyncio
import json
import multiprocessing
from copy import copy
from multiprocessing import Process
from typing import List

import grpc
import pytest
from docarray import Document, DocumentArray

from jina.clients.request import request_generator
from jina.enums import PollingType
from jina.proto import jina_pb2_grpc
from jina.serve.networking.utils import (
    get_available_services,
    get_default_grpc_options,
    send_request_sync,
    send_requests_sync,
)
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.head import HeadRuntime
from jina.types.request import Request
from jina.types.request.data import DataRequest
from tests.helper import _generate_pod_args


def test_regular_data_case():
    args = _generate_pod_args()
    args.polling = PollingType.ANY
    connection_list_dict = {0: [f'fake_ip:8080']}
    args.connection_list = json.dumps(connection_list_dict)
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(_create_test_data_message())

    assert response
    assert 'is-error' in dict(call.trailing_metadata())
    assert len(response.docs) == 1
    assert not handle_queue.empty()

    _destroy_runtime(args, cancel_event, runtime_thread)


@pytest.mark.parametrize('disable_reduce', [False, True])
def test_message_merging(disable_reduce):
    if not disable_reduce:
        args = _generate_pod_args()
    else:
        args = _generate_pod_args(['--no-reduce'])
    args.polling = PollingType.ALL
    connection_list_dict = {0: [f'ip1:8080'], 1: [f'ip2:8080'], 2: [f'ip3:8080']}
    args.connection_list = json.dumps(connection_list_dict)
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    assert handle_queue.empty()

    data_request = _create_test_data_message()
    result = send_requests_sync(
        [data_request, data_request], f'{args.host}:{args.port}'
    )
    assert result
    assert _queue_length(handle_queue) == 3
    assert len(result.response.docs) == 2 if disable_reduce else 1

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_uses_before_uses_after():
    args = _generate_pod_args()
    args.polling = PollingType.ALL
    args.uses_before_address = 'fake_address'
    args.uses_after_address = 'fake_address'
    connection_list_dict = {0: [f'ip1:8080'], 1: [f'ip2:8080'], 2: [f'ip3:8080']}
    args.connection_list = json.dumps(connection_list_dict)
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    assert handle_queue.empty()

    result = send_request_sync(_create_test_data_message(), f'{args.host}:{args.port}')
    assert result
    assert _queue_length(handle_queue) == 5  # uses_before + 3 workers + uses_after
    assert len(result.response.docs) == 1

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_decompress(monkeypatch):
    call_counts = multiprocessing.Manager().Queue()

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

    args = _generate_pod_args()
    args.polling = PollingType.ANY
    connection_list_dict = {0: [f'fake_ip:8080']}
    args.connection_list = json.dumps(connection_list_dict)
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(_create_test_data_message())

    assert response
    assert 'is-error' in dict(call.trailing_metadata())
    assert _queue_length_copy(call_counts) == 0
    assert len(response.docs) == 1
    assert _queue_length_copy(call_counts) == 1
    assert not handle_queue.empty()

    _destroy_runtime(args, cancel_event, runtime_thread)


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_dynamic_polling(polling):
    args = _generate_pod_args(
        [
            '--polling',
            json.dumps(
                {'/any': PollingType.ANY, '/all': PollingType.ALL, '*': polling}
            ),
            '--shards',
            str(2),
        ]
    )

    connection_list_dict = {0: [f'fake_ip:8080'], 1: [f'fake_ip:8080']}
    args.connection_list = json.dumps(connection_list_dict)

    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='all'), metadata=(('endpoint', '/all'),)
        )

    assert response
    assert _queue_length(handle_queue) == 2

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='any'), metadata=(('endpoint', '/any'),)
        )

    assert response
    assert _queue_length(handle_queue) == 3

    _destroy_runtime(args, cancel_event, runtime_thread)


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_base_polling(polling):
    args = _generate_pod_args(
        [
            '--polling',
            polling,
            '--shards',
            str(2),
        ]
    )
    connection_list_dict = {0: [f'fake_ip:8080'], 1: [f'fake_ip:8080']}
    args.connection_list = json.dumps(connection_list_dict)
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='all'), metadata=(('endpoint', '/all'),)
        )

    assert response
    assert _queue_length(handle_queue) == 2 if polling == 'all' else 1

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='any'), metadata=(('endpoint', '/any'),)
        )

    assert response
    assert _queue_length(handle_queue) == 4 if polling == 'all' else 2

    _destroy_runtime(args, cancel_event, runtime_thread)


@pytest.mark.asyncio
async def test_head_runtime_reflection():
    args = _generate_pod_args()
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=3.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    async with grpc.aio.insecure_channel(f'{args.host}:{args.port}') as channel:
        service_names = await get_available_services(channel)

    assert all(
        service_name in service_names
        for service_name in [
            'jina.JinaDataRequestRPC',
            'jina.JinaSingleDataRequestRPC',
        ]
    )

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_timeout_behaviour():
    args = _generate_pod_args(['--timeout-send', '100'])
    args.polling = PollingType.ANY
    connection_list_dict = {0: [f'fake_ip:8080']}
    args.connection_list = json.dumps(connection_list_dict)
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port}',
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(_create_test_data_message())

    assert response
    assert 'is-error' in dict(call.trailing_metadata())
    assert len(response.docs) == 1
    assert not handle_queue.empty()

    _destroy_runtime(args, cancel_event, runtime_thread)


def _create_test_data_message(counter=0, endpoint='/'):
    return list(
        request_generator(endpoint, DocumentArray([Document(text=str(counter))]))
    )[0]


def _create_runtime(args):
    handle_queue = multiprocessing.Queue()
    cancel_event = multiprocessing.Event()

    def start_runtime(runtime_args, handle_queue, cancel_event):
        def _send_requests_mock(
            request: List[Request],
            connection,
            endpoint,
            metadata: dict = None,
            timeout=1.0,
            retries=-1,
        ) -> asyncio.Task:
            async def mock_task_wrapper(new_requests, *args, **kwargs):
                handle_queue.put('mock_called')
                assert timeout == (
                    runtime_args.timeout_send / 1000 if timeout else None
                )
                await asyncio.sleep(0.1)
                return new_requests[0], grpc.aio.Metadata.from_tuple(
                    (('is-error', 'true'),)
                )

            return asyncio.create_task(mock_task_wrapper(request, connection))

        if not hasattr(runtime_args, 'name') or not runtime_args.name:
            runtime_args.name = 'testHead'
        with HeadRuntime(runtime_args, cancel_event=cancel_event) as runtime:
            runtime.connection_pool._send_requests = _send_requests_mock
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, handle_queue, cancel_event),
        daemon=True,
    )
    runtime_thread.start()
    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    return cancel_event, handle_queue, runtime_thread


def _destroy_runtime(args, cancel_event, runtime_thread):
    cancel_event.set()
    runtime_thread.join()
    assert not HeadRuntime.is_ready(f'{args.host}:{args.port}')


def _queue_length(queue: 'multiprocessing.Queue'):
    # Pops elements from the queue and counts them
    # This is used instead of multiprocessing.Queue.qsize() since it is not supported on MacOS
    length = 0
    q_elements = []
    while not queue.empty():
        q_elements.append(queue.get())
        length += 1
    for e in q_elements:
        queue.put_nowait(e)
    return length


def _queue_length_copy(queue: 'multiprocessing.Manager().Queue'):
    # Copies the queue and counts the elements in the copy
    # Used if the original queue needs to be preserved
    # This is used instead of multiprocessing.Queue.qsize() since it is not supported on MacOS
    c_queue = copy(queue)
    length = 0
    while not c_queue.empty():
        c_queue.get()
        length += 1
    return length
