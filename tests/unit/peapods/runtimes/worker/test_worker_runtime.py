import asyncio
import multiprocessing
import os
import time
from multiprocessing import Process
from threading import Event

import pytest

from jina import DocumentArray
from jina.clients.request import request_generator
from jina.parsers import set_pea_parser
from jina.peapods.networking import GrpcConnectionPool
from jina.peapods.runtimes.asyncio import AsyncNewLoopRuntime
from jina.peapods.runtimes.worker import WorkerRuntime
from jina.proto.jina_pb2 import DocumentArrayProto
from jina.types.document import Document
from jina.types.request.data import DataRequest


@pytest.mark.slow
@pytest.mark.timeout(5)
def test_worker_runtime():
    args = set_pea_parser().parse_args([])

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port_in}',
        ready_or_shutdown_event=Event(),
    )

    response = GrpcConnectionPool.send_request_sync(
        _create_test_data_message(),
        f'{args.host}:{args.port_in}',
    )

    cancel_event.set()
    runtime_thread.join()

    assert response

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port_in}')


@pytest.mark.slow
@pytest.mark.timeout(10)
@pytest.mark.asyncio
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='Graceful shutdown is not working at the moment',
)
# TODO: This test should work, it does not
async def test_worker_runtime_graceful_shutdown():
    args = set_pea_parser().parse_args([])

    cancel_event = multiprocessing.Event()
    handler_closed_event = multiprocessing.Event()
    slow_executor_block_time = 1.0
    pending_requests = 5

    def start_runtime(args, cancel_event, handler_closed_event):
        with WorkerRuntime(args, cancel_event) as runtime:
            runtime._data_request_handler.handle = lambda *args, **kwargs: time.sleep(
                slow_executor_block_time
            )
            runtime._data_request_handler.close = (
                lambda *args, **kwargs: handler_closed_event.set()
            )

            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event, handler_closed_event),
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port_in}',
        ready_or_shutdown_event=Event(),
    )

    request_start_time = time.time()

    async def task_wrapper(adress, messages_received):
        request = _create_test_data_message(len(messages_received))
        data_stub, control_stub, channel = GrpcConnectionPool.create_async_channel_stub(
            adress
        )
        await data_stub.process_data(request)
        await channel.close()
        messages_received.append(request)

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

    runtime_thread.terminate()

    assert not handler_closed_event.is_set()
    runtime_thread.join()

    for future in asyncio.as_completed(tasks):
        _ = await future

    assert pending_requests == sent_requests
    assert sent_requests == len(messages_received)

    assert (
        time.time() - request_start_time >= slow_executor_block_time * pending_requests
    )
    assert handler_closed_event.is_set()
    assert not WorkerRuntime.is_ready(f'{args.host}:{args.port_in}')


def _create_test_data_message(counter=0):
    return list(request_generator('/', DocumentArray([Document(text=str(counter))])))[0]
