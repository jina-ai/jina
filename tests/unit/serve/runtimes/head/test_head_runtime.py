import asyncio
import json
import multiprocessing
from copy import copy, deepcopy
from multiprocessing import Process
from typing import List

import grpc
import pytest
from grpc import RpcError

from jina import DocumentArray, Document
from jina.clients.request import request_generator
from jina.enums import PollingType
from jina.parsers import set_pea_parser
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.head import HeadRuntime
from jina.proto import jina_pb2_grpc
from jina.types.request import Request
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest


def test_regular_data_case():
    args = set_pea_parser().parse_args([])
    args.polling = PollingType.ANY
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    _add_worker(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port_in}',
        options=GrpcConnectionPool.get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(_create_test_data_message())

    assert response
    assert 'is-error' in dict(call.trailing_metadata())
    assert len(response.docs) == 1
    assert not handle_queue.empty()

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_control_message_processing():
    args = set_pea_parser().parse_args([])
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    # no connection registered yet
    with pytest.raises(RpcError):
        GrpcConnectionPool.send_request_sync(
            _create_test_data_message(), f'{args.host}:{args.port_in}'
        )

    _add_worker(args, 'ip1')
    # after adding a connection, sending should work
    result = GrpcConnectionPool.send_request_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
    assert result

    _remove_worker(args, 'ip1')
    # after removing the connection again, sending does not work anymore
    with pytest.raises(RpcError):
        GrpcConnectionPool.send_request_sync(
            _create_test_data_message(), f'{args.host}:{args.port_in}'
        )

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_message_merging():
    args = set_pea_parser().parse_args([])
    args.polling = PollingType.ALL
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    assert handle_queue.empty()
    _add_worker(args, 'ip1', shard_id=0)
    _add_worker(args, 'ip2', shard_id=1)
    _add_worker(args, 'ip3', shard_id=2)
    assert handle_queue.empty()

    result = GrpcConnectionPool.send_request_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
    assert result
    assert _queue_length(handle_queue) == 3
    assert len(result.response.docs) == 1

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_uses_before_uses_after():
    args = set_pea_parser().parse_args([])
    args.polling = PollingType.ALL
    args.uses_before_address = 'fake_address'
    args.uses_after_address = 'fake_address'
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    assert handle_queue.empty()
    _add_worker(args, 'ip1', shard_id=0)
    _add_worker(args, 'ip2', shard_id=1)
    _add_worker(args, 'ip3', shard_id=2)
    assert handle_queue.empty()

    result = GrpcConnectionPool.send_request_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
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

    args = set_pea_parser().parse_args([])
    args.polling = PollingType.ANY
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    _add_worker(args)

    with grpc.insecure_channel(
        f'{args.host}:{args.port_in}',
        options=GrpcConnectionPool.get_default_grpc_options(),
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
    args = set_pea_parser().parse_args(
        [
            '--polling',
            json.dumps(
                {'/any': PollingType.ANY, '/all': PollingType.ALL, '*': polling}
            ),
            '--shards',
            str(2),
        ]
    )
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    _add_worker(args, shard_id=0)
    _add_worker(args, shard_id=1)

    with grpc.insecure_channel(
        f'{args.host}:{args.port_in}',
        options=GrpcConnectionPool.get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='all'), metadata=(('endpoint', '/all'),)
        )

    assert response
    assert _queue_length(handle_queue) == 2

    with grpc.insecure_channel(
        f'{args.host}:{args.port_in}',
        options=GrpcConnectionPool.get_default_grpc_options(),
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
    args = set_pea_parser().parse_args(
        [
            '--polling',
            polling,
            '--shards',
            str(2),
        ]
    )
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    _add_worker(args, shard_id=0)
    _add_worker(args, shard_id=1)

    with grpc.insecure_channel(
        f'{args.host}:{args.port_in}',
        options=GrpcConnectionPool.get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='all'), metadata=(('endpoint', '/all'),)
        )

    assert response
    assert _queue_length(handle_queue) == 2 if polling == 'all' else 1

    with grpc.insecure_channel(
        f'{args.host}:{args.port_in}',
        options=GrpcConnectionPool.get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(
            _create_test_data_message(endpoint='any'), metadata=(('endpoint', '/any'),)
        )

    assert response
    assert _queue_length(handle_queue) == 4 if polling == 'all' else 2

    _destroy_runtime(args, cancel_event, runtime_thread)


def _create_test_data_message(counter=0, endpoint='/'):
    return list(
        request_generator(endpoint, DocumentArray([Document(text=str(counter))]))
    )[0]


def _create_runtime(args):
    handle_queue = multiprocessing.Queue()
    cancel_event = multiprocessing.Event()

    def start_runtime(args, handle_queue, cancel_event):
        def _send_requests_mock(
            request: List[Request], connection, endpoint
        ) -> asyncio.Task:
            async def mock_task_wrapper(new_requests, *args, **kwargs):
                handle_queue.put('mock_called')
                await asyncio.sleep(0.1)
                return new_requests[0], grpc.aio.Metadata.from_tuple(
                    (('is-error', 'true'),)
                )

            return asyncio.create_task(mock_task_wrapper(request, connection))

        if not hasattr(args, 'name') or not args.name:
            args.name = 'testHead'
        with HeadRuntime(args, cancel_event) as runtime:
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
        ctrl_address=f'{args.host}:{args.port_in}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    return cancel_event, handle_queue, runtime_thread


def _add_worker(args, ip='fake_ip', shard_id=None):
    activate_msg = ControlRequest(command='ACTIVATE')
    activate_msg.add_related_entity('worker', ip, 8080, shard_id)
    assert GrpcConnectionPool.send_request_sync(
        activate_msg, f'{args.host}:{args.port_in}'
    )


def _remove_worker(args, ip='fake_ip', shard_id=None):
    activate_msg = ControlRequest(command='DEACTIVATE')
    activate_msg.add_related_entity('worker', ip, 8080, shard_id)
    assert GrpcConnectionPool.send_request_sync(
        activate_msg, f'{args.host}:{args.port_in}'
    )


def _destroy_runtime(args, cancel_event, runtime_thread):
    cancel_event.set()
    runtime_thread.join()
    assert not HeadRuntime.is_ready(f'{args.host}:{args.port_in}')


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
