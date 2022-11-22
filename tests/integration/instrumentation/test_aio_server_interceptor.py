import multiprocessing
from multiprocessing import Process
from threading import Event

import grpc
import pytest
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection
from opentelemetry.trace import NoOpTracer
from opentelemetry.instrumentation.grpc._aio_server import OpenTelemetryAioServerInterceptor

from jina.helper import random_port
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.proto import jina_pb2, jina_pb2_grpc
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime


def test_default_health_servicer(jaeger_port, otlp_collector, otlp_receiver_port):
    cancel_event = multiprocessing.Event()

    def start_gateway(args, cancel_event):
        with GatewayRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    gateway_args = set_gateway_parser().parse_args([])
    gateway_args.tracing = True
    gateway_args.traces_exporter_host = 'localhost'
    gateway_args.traces_exporter_port = int(otlp_receiver_port)
    gatway_thread = Process(
        target=start_gateway,
        args=(
            gateway_args,
            cancel_event,
        ),
        daemon=True,
    )

    worker_args = set_pod_parser().parse_args([])
    worker_args.name = 'worker'
    worker_args.tracing = True
    worker_args.traces_exporter_host = 'localhost'
    worker_args.traces_exporter_port = int(otlp_receiver_port)

    def start_worker(args, cancel_event):
        with WorkerRuntime(args, cancel_event=cancel_event) as runtime:
            runtime.run_forever()

    worker_thread = Process(
        target=start_worker,
        args=(worker_args, cancel_event),
        daemon=True,
    )

    def check_health(target):
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=target,
            ready_or_shutdown_event=Event(),
        )

    gatway_thread.start()
    worker_thread.start()
    try:
        target = f'{gateway_args.host}:{gateway_args.port[0]}'
        p = multiprocessing.Process(target=check_health, args=(target,))
        p.start()
        p.join()
        response = GrpcConnectionPool.send_health_check_sync(target)
        assert response.status == 1

        target = f'{worker_args.host}:{worker_args.port}'
        p = multiprocessing.Process(target=check_health, args=(target,))
        p.start()
        p.join()
        response = GrpcConnectionPool.send_health_check_sync(target)
        assert response.status == 1
    finally:
        cancel_event.set()
        gatway_thread.join()
        worker_thread.join()
