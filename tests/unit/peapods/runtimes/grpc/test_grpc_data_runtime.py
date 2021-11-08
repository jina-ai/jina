import asyncio
import multiprocessing
import os
import time
from multiprocessing import Process
from threading import Event, Thread

import pytest

from jina import DocumentArray
from jina.clients.request import request_generator
from jina.parsers import set_pea_parser
from jina.peapods.grpc import Grpclet
from jina.peapods.runtimes.grpc import GRPCDataRuntime
from jina.types.document import Document
from jina.types.message import Message


@pytest.mark.slow
@pytest.mark.timeout(5)
def test_grpc_data_runtime(mocker):
    args = set_pea_parser().parse_args([])
    handle_mock = multiprocessing.Event()

    cancel_event = multiprocessing.Event()

    def start_runtime(args, handle_mock, cancel_event):
        with GRPCDataRuntime(args, cancel_event) as runtime:
            runtime._data_request_handler.handle = (
                lambda *args, **kwargs: handle_mock.set()
            )
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, handle_mock, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert GRPCDataRuntime.wait_for_ready_or_shutdown(
        timeout=5.0, ctrl_address=f'{args.host}:{args.port_in}', shutdown_event=Event()
    )

    Grpclet._create_grpc_stub(f'{args.host}:{args.port_in}', is_async=False).Call(
        _create_test_data_message()
    )
    time.sleep(0.1)
    assert handle_mock.is_set()

    GRPCDataRuntime.cancel(cancel_event)
    runtime_thread.join()

    assert not GRPCDataRuntime.is_ready(f'{args.host}:{args.port_in}')


@pytest.mark.slow
@pytest.mark.timeout(10)
@pytest.mark.parametrize('close_method', ['TERMINATE', 'CANCEL'])
def test_grpc_data_runtime_waits_for_pending_messages_shutdown(close_method):
    args = set_pea_parser().parse_args([])

    cancel_event = multiprocessing.Event()
    handler_closed_event = multiprocessing.Event()
    slow_executor_block_time = 1.0
    pending_requests = 3
    sent_queue = multiprocessing.Queue()

    def start_runtime(args, cancel_event, sent_queue, handler_closed_event):
        with GRPCDataRuntime(args, cancel_event) as runtime:
            runtime._data_request_handler.handle = lambda *args, **kwargs: time.sleep(
                slow_executor_block_time
            )
            runtime._data_request_handler.close = (
                lambda *args, **kwargs: handler_closed_event.set()
            )

            async def mock(msg):
                sent_queue.put('')

            runtime._grpclet.send_message = mock

            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event, sent_queue, handler_closed_event),
        daemon=True,
    )
    runtime_thread.start()

    assert GRPCDataRuntime.wait_for_ready_or_shutdown(
        timeout=5.0, ctrl_address=f'{args.host}:{args.port_in}', shutdown_event=Event()
    )

    request_start_time = time.time()
    for i in range(pending_requests):
        Grpclet._create_grpc_stub(f'{args.host}:{args.port_in}', is_async=False).Call(
            _create_test_data_message()
        )
    time.sleep(0.1)

    if close_method == 'TERMINATE':
        runtime_thread.terminate()
    else:
        GRPCDataRuntime.cancel(cancel_event)
    assert not handler_closed_event.is_set()
    runtime_thread.join()

    assert (
        time.time() - request_start_time >= slow_executor_block_time * pending_requests
    )
    assert sent_queue.qsize() == pending_requests
    assert handler_closed_event.is_set()

    assert not GRPCDataRuntime.is_ready(f'{args.host}:{args.port_in}')


@pytest.mark.slow
@pytest.mark.timeout(10)
@pytest.mark.parametrize('close_method', ['TERMINATE', 'CANCEL'])
@pytest.mark.asyncio
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='Graceful shutdown is not working at the moment',
)
# TODO: This test should work, it does not
async def test_grpc_data_runtime_graceful_shutdown(close_method):
    args = set_pea_parser().parse_args([])

    cancel_event = multiprocessing.Event()
    handler_closed_event = multiprocessing.Event()
    slow_executor_block_time = 1.0
    pending_requests = 5
    sent_queue = multiprocessing.Queue()

    def start_runtime(args, cancel_event, sent_queue, handler_closed_event):
        with GRPCDataRuntime(args, cancel_event) as runtime:
            runtime._data_request_handler.handle = lambda *args, **kwargs: time.sleep(
                slow_executor_block_time
            )
            runtime._data_request_handler.close = (
                lambda *args, **kwargs: handler_closed_event.set()
            )

            async def mock(msg):
                sent_queue.put('')

            runtime._grpclet.send_message = mock

            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event, sent_queue, handler_closed_event),
        daemon=True,
    )
    runtime_thread.start()

    assert GRPCDataRuntime.wait_for_ready_or_shutdown(
        timeout=5.0, ctrl_address=f'{args.host}:{args.port_in}', shutdown_event=Event()
    )

    request_start_time = time.time()

    async def task_wrapper(adress, messages_received):
        msg = _create_test_data_message(len(messages_received))
        await Grpclet._create_grpc_stub(adress).Call(msg)
        messages_received.append(msg)

    sent_requests = 0
    messages_received = []
    tasks = []
    for i in range(pending_requests):
        tasks.append(
            asyncio.create_task(
                task_wrapper(f'{args.host}:{args.port_in}', messages_received)
            )
        )
        sent_requests += 1

    await asyncio.sleep(1.0)

    if close_method == 'TERMINATE':
        runtime_thread.terminate()
    else:
        GRPCDataRuntime.cancel(cancel_event)

    assert not handler_closed_event.is_set()
    runtime_thread.join()

    assert pending_requests == sent_requests
    assert sent_requests == len(messages_received)
    assert sent_queue.qsize() == pending_requests

    assert (
        time.time() - request_start_time >= slow_executor_block_time * pending_requests
    )
    assert handler_closed_event.is_set()
    assert not GRPCDataRuntime.is_ready(f'{args.host}:{args.port_in}')


def _create_test_data_message(counter=0):
    req = list(request_generator('/', DocumentArray([Document(text=str(counter))])))[0]
    msg = Message(None, req, 'test', '123')
    return msg
