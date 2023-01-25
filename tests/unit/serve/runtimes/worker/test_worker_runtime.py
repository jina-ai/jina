import asyncio
import multiprocessing
import socket
import time
from multiprocessing import Process
from threading import Event

import grpc
import pytest
import requests as req

from jina import Document, DocumentArray, Executor, requests
from jina.clients.request import request_generator
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.networking.utils import (
    get_available_services,
    get_default_grpc_options,
    send_request_async,
)
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
from tests.helper import _generate_pod_args


@pytest.mark.slow
@pytest.mark.timeout(5)
def test_worker_runtime():
    args = _generate_pod_args()

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    target = f'{args.host}:{args.port}'
    with grpc.insecure_channel(
        target,
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(_create_test_data_message())

    cancel_event.set()
    runtime_thread.join()

    assert response

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


class AsyncSlowNewDocsExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._count = 0

    @requests
    async def foo(self, docs, **kwargs):
        self._count += 1
        current_count = self._count
        if current_count % 2 == 0:
            await asyncio.sleep(0.1)
        return DocumentArray([Document(text=str(current_count))])


class SlowNewDocsExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._count = 0

    @requests
    def foo(self, docs, **kwargs):
        self._count += 1
        current_count = self._count
        if current_count % 2 == 0:
            time.sleep(0.1)
        return DocumentArray([Document(text=str(current_count))])


@pytest.mark.slow
@pytest.mark.timeout(5)
@pytest.mark.asyncio
@pytest.mark.parametrize('uses', ['AsyncSlowNewDocsExecutor', 'SlowNewDocsExecutor'])
async def test_worker_runtime_slow_async_exec(uses):
    args = _generate_pod_args(['--uses', uses])

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    target = f'{args.host}:{args.port}'
    results = []
    async with grpc.aio.insecure_channel(
        target,
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        tasks = []
        for i in range(10):

            async def task_wrapper():
                return await stub.process_single_data(_create_test_data_message())

            tasks.append(asyncio.create_task(task_wrapper()))
        for future in asyncio.as_completed(tasks):
            t = await future
            results.append(t.docs[0].text)

    cancel_event.set()
    runtime_thread.join()

    if uses == 'AsyncSlowNewDocsExecutor':
        assert results == ['1', '3', '5', '7', '9', '2', '4', '6', '8', '10']
    else:
        assert results == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


@pytest.mark.slow
@pytest.mark.timeout(10)
def test_error_in_worker_runtime(monkeypatch):
    args = _generate_pod_args()

    cancel_event = multiprocessing.Event()

    def fail(*args, **kwargs):
        raise RuntimeError('intentional error')

    monkeypatch.setattr(WorkerRequestHandler, 'handle', fail)

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    target = f'{args.host}:{args.port}'
    with grpc.insecure_channel(
        target,
        options=get_default_grpc_options(),
    ) as channel:
        stub = jina_pb2_grpc.JinaSingleDataRequestRPCStub(channel)
        response, call = stub.process_single_data.with_call(_create_test_data_message())

    assert response.header.status.code == jina_pb2.StatusProto.ERROR
    assert 'is-error' in dict(call.trailing_metadata())
    cancel_event.set()
    runtime_thread.join()

    assert response

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


class SlowInitExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        time.sleep(5.0)

    @requests
    def foo(self, docs, **kwargs):
        return docs


@pytest.mark.timeout(10)
@pytest.mark.asyncio
@pytest.mark.skip
async def test_worker_runtime_slow_init_exec():
    args = _generate_pod_args(['--uses', 'SlowInitExecutor'])

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_started = time.time()
    runtime_thread.start()

    # wait a bit to the worker runtime has a chance to finish some things, but not the Executor init (5 secs)
    time.sleep(1.0)

    # try to connect a TCP socket to the gRPC server
    # this should only succeed after the Executor is ready, which should be after 5 seconds
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        connected = False
        while not connected:
            try:
                s.connect((args.host, args.port))
                connected = True
            except:
                time.sleep(0.2)

    # Executor sleeps 5 seconds, so at least 5 seconds need to have elapsed here
    assert time.time() - runtime_started > 5.0

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=3.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    result = await send_request_async(
        _create_test_data_message(), f'{args.host}:{args.port}', timeout=1.0
    )

    assert len(result.docs) == 1

    cancel_event.set()
    runtime_thread.join()

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


@pytest.mark.asyncio
async def test_worker_runtime_reflection():
    args = _generate_pod_args()

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=3.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
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

    cancel_event.set()
    runtime_thread.join()

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


def _create_test_data_message(counter=0):
    return list(request_generator('/', DocumentArray([Document(text=str(counter))])))[0]


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.timeout(5)
@pytest.mark.skip
async def test_decorator_monitoring(port_generator):
    from jina import monitor

    class DummyExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            self._proces(docs)
            self.process_2(docs)

        @monitor(name='metrics_name', documentation='metrics description')
        def _proces(self, docs):
            ...

        @monitor()
        def process_2(self, docs):
            ...

    port = port_generator()
    args = _generate_pod_args(
        ['--monitoring', '--port-monitoring', str(port), '--uses', 'DummyExecutor']
    )

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    await send_request_async(
        _create_test_data_message(), f'{args.host}:{args.port}', timeout=1.0
    )

    resp = req.get(f'http://localhost:{port}/')
    assert f'jina_metrics_name_count{{runtime_name="None"}} 1.0' in str(resp.content)

    cancel_event.set()
    runtime_thread.join()

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.timeout(5)
@pytest.mark.skip
async def test_decorator_monitoring(port_generator):
    class DummyExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):

            with self.monitor(
                name='process_seconds', documentation='process time in seconds '
            ):
                self._proces(docs)

            with self.monitor(
                name='process_2_seconds', documentation='process 2 time in seconds '
            ):
                self.process_2(docs)

        def _proces(self, docs):
            ...

        def process_2(self, docs):
            ...

    port = port_generator()
    args = _generate_pod_args(
        ['--monitoring', '--port-monitoring', str(port), '--uses', 'DummyExecutor']
    )

    cancel_event = multiprocessing.Event()

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    await send_request_async(
        _create_test_data_message(), f'{args.host}:{args.port}', timeout=1.0
    )

    resp = req.get(f'http://localhost:{port}/')
    assert f'jina_process_seconds_count{{runtime_name="None"}} 1.0' in str(resp.content)

    cancel_event.set()
    runtime_thread.join()

    assert not AsyncNewLoopRuntime.is_ready(f'{args.host}:{args.port}')


@pytest.mark.slow
@pytest.mark.timeout(10)
async def test_error_in_worker_runtime_with_exit_on_exceptions(monkeypatch):
    args = _generate_pod_args(['--exit-on-exceptions', 'RuntimeError'])

    cancel_event = multiprocessing.Event()

    def fail(*args, **kwargs):
        raise RuntimeError('intentional error')

    monkeypatch.setattr(WorkerRequestHandler, 'handle', fail)

    def start_runtime(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    runtime_thread = Process(
        target=start_runtime,
        args=(args, cancel_event),
        daemon=True,
    )
    runtime_thread.start()

    assert AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'{args.host}:{args.port}',
        ready_or_shutdown_event=Event(),
    )

    target = f'{args.host}:{args.port}'
    response = await send_request_async(_create_test_data_message(), target)
    assert response.header.status.code == jina_pb2.StatusProto.ERROR

    cancel_event.set()
    runtime_thread.join()

    assert not AsyncNewLoopRuntime.is_ready(target)
