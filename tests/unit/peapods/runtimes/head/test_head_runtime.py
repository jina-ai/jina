import asyncio
import multiprocessing
from multiprocessing import Process
from typing import List

import pytest
from grpc import RpcError

from jina import DocumentArray, Document
from jina.clients.request import request_generator
from jina.enums import PollingType
from jina.parsers import set_pea_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.runtimes.asyncio import AsyncNewLoopRuntime
from jina.peapods.runtimes.head import HeadRuntime
from jina.types.message import Message
from jina.types.message.common import ControlMessage


def test_regular_data_case():
    args = set_pea_parser().parse_args([])
    args.polling = PollingType.ANY
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    _add_worker(args)
    result = GrpcConnectionPool.send_message_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
    assert result
    assert len(result.response.docs) == 1
    assert not handle_queue.empty()

    _destroy_runtime(args, cancel_event, runtime_thread)


def test_control_message_processing():
    args = set_pea_parser().parse_args([])
    cancel_event, handle_queue, runtime_thread = _create_runtime(args)

    # no connection registered yet
    with pytest.raises(RpcError):
        GrpcConnectionPool.send_message_sync(
            _create_test_data_message(), f'{args.host}:{args.port_in}'
        )

    _add_worker(args, 'ip1')
    # after adding a connection, sending should work
    result = GrpcConnectionPool.send_message_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
    assert result

    _remove_worker(args, 'ip1')
    # after removing the connection again, sending does not work anymore
    with pytest.raises(RpcError):
        GrpcConnectionPool.send_message_sync(
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

    result = GrpcConnectionPool.send_message_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
    assert result
    assert handle_queue.qsize() == 3
    assert len(result.response.docs) == 3

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

    result = GrpcConnectionPool.send_message_sync(
        _create_test_data_message(), f'{args.host}:{args.port_in}'
    )
    assert result
    assert handle_queue.qsize() == 5  # uses_before + 3 workers + uses_after
    assert (
        len(result.response.docs) == 1
    )  # mock uses_after just returns a single message

    _destroy_runtime(args, cancel_event, runtime_thread)


def _create_test_data_message(counter=0):
    req = list(request_generator('/', DocumentArray([Document(text=str(counter))])))[0]
    msg = Message(None, req)
    return msg


def _create_runtime(args):
    handle_queue = multiprocessing.Queue()
    cancel_event = multiprocessing.Event()

    def start_runtime(args, handle_queue, cancel_event):
        def _send_messages_mock(messages: List[Message], connection) -> asyncio.Task:
            async def mock_task_wrapper(new_messages, *args, **kwargs):
                handle_queue.put('mock_called')
                await asyncio.sleep(0.1)
                return new_messages[0]

            return asyncio.create_task(mock_task_wrapper(messages, connection))

        with HeadRuntime(args, cancel_event) as runtime:
            runtime.connection_pool._send_messages = _send_messages_mock
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
    activate_msg = ControlMessage(command='ACTIVATE')
    activate_msg.add_related_entity('worker', ip, 8080, shard_id)
    assert GrpcConnectionPool.send_message_sync(
        activate_msg, f'{args.host}:{args.port_in}'
    )


def _remove_worker(args, ip='fake_ip', shard_id=None):
    activate_msg = ControlMessage(command='DEACTIVATE')
    activate_msg.add_related_entity('worker', ip, 8080, shard_id)
    assert GrpcConnectionPool.send_message_sync(
        activate_msg, f'{args.host}:{args.port_in}'
    )


def _destroy_runtime(args, cancel_event, runtime_thread):
    cancel_event.set()
    runtime_thread.join()
    assert not HeadRuntime.is_ready(f'{args.host}:{args.port_in}')
