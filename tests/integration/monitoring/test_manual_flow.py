import multiprocessing
import time

import pytest
import requests as req
from docarray import Document, DocumentArray

from jina import Executor, Flow, requests
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import _generate_pod_args


def _create_worker_runtime(port, name='', executor=None, port_monitoring=None):
    args = _generate_pod_args()
    args.port = port
    args.name = name

    if port_monitoring:
        args.monitoring = True
        args.port_monitoring = port_monitoring

    if executor:
        args.uses = executor

    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(
    graph_description, pod_addresses, port, port_monitoring, protocol, retries=-1
):
    args = set_gateway_parser().parse_args(
        [
            '--graph-description',
            graph_description,
            '--deployments-addresses',
            pod_addresses,
            '--port',
            str(port),
            '--retries',
            str(retries),
            '--monitoring',
            '--port-monitoring',
            str(port_monitoring),
            '--protocol',
            protocol,
        ]
    )
    args.port_monitoring = port_monitoring
    with GatewayRuntime(args) as runtime:
        runtime.run_forever()


def _create_worker(port, port_monitoring=None):
    # create a single worker runtime
    p = multiprocessing.Process(
        target=_create_worker_runtime,
        args=(port,),
        kwargs={'port_monitoring': port_monitoring},
        daemon=True,
    )
    p.start()
    time.sleep(0.1)
    return p


def _create_gateway(port, port_monitoring, graph, pod_addr, protocol, retries=-1):
    # create a single worker runtime
    # create a single gateway runtime
    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph, pod_addr, port, port_monitoring, protocol, retries),
        daemon=True,
    )
    p.start()
    time.sleep(0.1)
    return p


def _send_request(gateway_port, protocol, n_docs=2):
    """send request to gateway and see what happens"""
    from jina.clients import Client

    c = Client(host='localhost', port=gateway_port, protocol=protocol)
    return c.post(
        '/foo',
        inputs=[Document(text='hi') for _ in range(n_docs)],
        request_size=1,
        return_responses=True,
        continue_on_error=True,
    )


@pytest.mark.asyncio
async def test_kill_worker(port_generator):
    # create gateway and workers manually, then terminate worker process to provoke an error
    worker_port = port_generator()
    worker_monitoring_port = port_generator()
    gateway_port = port_generator()
    gateway_monitoring_port = port_generator()

    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    worker_process = _create_worker(worker_port, port_monitoring=worker_monitoring_port)
    time.sleep(0.1)
    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    gateway_process = _create_gateway(
        gateway_port, gateway_monitoring_port, graph_description, pod_addresses, 'grpc'
    )

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    try:
        # send first successful request
        p = multiprocessing.Process(
            target=_send_request,
            args=(gateway_port, 'grpc'),
            kwargs={'n_docs': 1},
            daemon=True,
        )
        p.start()
        p.join()

        assert p.exitcode == 0

        worker_process.terminate()  # kill worker
        worker_process.join()

        # send second request, should fail
        p = multiprocessing.Process(
            target=_send_request,
            args=(gateway_port, 'grpc'),
            kwargs={'n_docs': 1},
            daemon=True,
        )
        p.start()
        p.join()

        assert p.exitcode != 0

        # 1 request failed, 1 request successful
        resp = req.get(f'http://localhost:{gateway_monitoring_port}/')
        assert f'jina_successful_requests_total{{runtime_name="gateway"}} 1.0' in str(
            resp.content
        )

        assert f'jina_failed_requests_total{{runtime_name="gateway"}} 1.0' in str(
            resp.content
        )

    except Exception:
        raise
    finally:  # clean up runtimes
        gateway_process.terminate()
        gateway_process.join()


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_pending_requests_with_connection_error(port_generator, protocol):
    runtime_name = 'gateway'
    gateway_port = port_generator()
    worker_port = port_generator()
    port_monitoring = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    gateway_process = _create_gateway(
        gateway_port, port_monitoring, graph_description, pod_addresses, protocol
    )

    time.sleep(1.0)

    GatewayRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
        protocol=protocol,
    )

    try:
        p = multiprocessing.Process(
            target=_send_request, args=(gateway_port, protocol), daemon=True
        )
        p.start()
        p.join()
        time.sleep(2)
        _assert_pending_value('0.0', runtime_name, port_monitoring)
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        gateway_process.join()


def _assert_pending_value(val: str, runtime_name, port):
    resp = req.get(f'http://localhost:{port}/')
    assert resp.status_code == 200
    assert (
        f'jina_number_of_pending_requests{{runtime_name="{runtime_name}"}} {val}'
        in str(resp.content)
    )


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
@pytest.mark.parametrize('failure_in_executor', [False, True])
def test_pending_request(port_generator, failure_in_executor, protocol):
    port0 = port_generator()
    port1 = port_generator()
    runtime_name = 'gateway/rep-0'

    class SlowExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            time.sleep(5)
            if failure_in_executor:
                raise Exception

    with Flow(monitoring=True, port_monitoring=port0, protocol=protocol).add(
        uses=SlowExecutor, port_monitoring=port1
    ) as f:

        def _send_request():
            f.search(inputs=DocumentArray.empty(size=1), continue_on_error=True)

        p_send = multiprocessing.Process(target=_send_request, daemon=True)
        _assert_pending_value('0.0', runtime_name, port0)

        p_send.start()
        time.sleep(3)

        _assert_pending_value('1.0', runtime_name, port0)

        p_send.join()
        assert p_send.exitcode == 0
        _assert_pending_value('0.0', runtime_name, port0)
