import multiprocessing
import time

import pytest
import requests as req
from docarray import Document, DocumentArray

from jina import Executor, Flow, requests
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.serve.runtimes.gateway.http import HTTPGatewayRuntime
from jina.serve.runtimes.gateway.websocket import WebSocketGatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime


@pytest.fixture()
def executor():
    class DummyExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            ...

        @requests(on='/bar')
        def bar(self, docs, **kwargs):
            ...

    return DummyExecutor


@pytest.fixture()
def failing_executor():
    class FailingExecutor(Executor):
        def __init__(self, *args, **kwargs):
            super(FailingExecutor, self).__init__(*args, **kwargs)
            self.cnt = 0

        @requests(on='/fail')
        def fail(self, docs, **kwargs):
            self.cnt += 1
            if self.cnt % 2 == 1:
                raise Exception()

        @requests(on='/timeout')
        def timeout(self, docs, **kwargs):
            time.sleep(3)

    return FailingExecutor


def test_enable_monitoring_deployment(port_generator, executor):
    port1 = port_generator()
    port2 = port_generator()

    with Flow().add(uses=executor, port_monitoring=port1, monitoring=True).add(
        uses=executor, port_monitoring=port2, monitoring=True
    ) as f:
        for port in [port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        for meth in ['bar', 'foo']:
            f.post(f'/{meth}', inputs=DocumentArray())
            resp = req.get(f'http://localhost:{port2}/')
            assert (
                f'process_request_seconds_created{{executor="DummyExecutor",executor_endpoint="/{meth}",runtime_name="executor1/rep-0"}}'
                in str(resp.content)
            )
            assert f'jina_number_of_successful_requests_total' in str(resp.content)
            assert f'jina_number_of_failed_requests_total' in str(resp.content)


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_enable_monitoring_gateway(protocol, port_generator, executor):
    port0 = port_generator()
    port1 = port_generator()
    port2 = port_generator()

    with Flow(protocol=protocol, monitoring=True, port_monitoring=port0).add(
        uses=executor, port_monitoring=port1
    ).add(uses=executor, port_monitoring=port2) as f:
        for port in [port0, port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port0}/')
        assert f'jina_receiving_request_seconds' in str(resp.content)
        assert f'jina_sending_request_seconds' in str(resp.content)
        assert f'jina_number_of_successful_requests_total' in str(resp.content)
        assert f'jina_number_of_failed_requests_total' in str(resp.content)


def test_monitoring_head(port_generator, executor):
    n_shards = 2
    port_shards_list = [port_generator() for _ in range(n_shards)]
    port_head = port_generator()
    port_monitoring = ','.join([str(port) for port in [port_head] + port_shards_list])
    port1 = port_generator()

    f = Flow(monitoring=True, port_monitoring=port1).add(
        uses=executor, port_monitoring=port_monitoring, shards=n_shards
    )

    assert f._deployment_nodes['executor0'].head_port_monitoring == port_head

    unique_port_exposed = set(
        [
            pod[0].port_monitoring
            for key, pod in f._deployment_nodes['executor0'].pod_args['pods'].items()
        ]
    )

    assert unique_port_exposed == set(port_shards_list)
    with f:
        for port in [port_head, port1] + port_shards_list:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port_head}/')
        assert f'jina_receiving_request_seconds' in str(resp.content)
        assert f'jina_sending_request_seconds' in str(resp.content)


def test_monitoring_head_few_port(port_generator, executor):
    n_shards = 2
    port1 = port_generator()
    port2 = port_generator()

    f = Flow(monitoring=True, port_monitoring=port1).add(
        uses=executor, port_monitoring=port2, shards=n_shards
    )

    assert f._deployment_nodes['executor0'].head_port_monitoring == port2

    unique_port_exposed = set(
        [
            pod[0].port_monitoring
            for key, pod in f._deployment_nodes['executor0'].pod_args['pods'].items()
        ]
    )
    with f:
        for port in [port2, port1]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200


def test_monitoring_replicas_and_shards(port_generator, executor):
    n_shards = 2
    n_replicas = 3
    port_shards_list = [port_generator() for _ in range(n_shards * n_replicas)]
    port_head = port_generator()
    port_monitoring = ','.join([str(port) for port in [port_head] + port_shards_list])
    port1 = port_generator()

    f = Flow(monitoring=True, port_monitoring=port1).add(
        uses=executor,
        port_monitoring=port_monitoring,
        shards=n_shards,
        replicas=n_replicas,
    )

    assert f._deployment_nodes['executor0'].head_port_monitoring == port_head

    unique_port_exposed = set(
        [
            pod.port_monitoring
            for _, deployment in f._deployment_nodes.items()
            for _, list_pod in deployment.pod_args['pods'].items()
            for pod in list_pod
        ]
    )

    assert unique_port_exposed == set(port_shards_list)

    with f:

        for port in port_shards_list:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200
            assert f'process_request_seconds' in str(resp.content)
            assert f'jina_number_of_successful_requests_total' in str(resp.content)
            assert f'jina_number_of_failed_requests_total' in str(resp.content)

        for port in [port_head, port1]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port_head}/')
        assert f'jina_receiving_request_seconds' in str(resp.content)
        assert f'jina_sending_request_seconds' in str(resp.content)


def test_document_processed_total(port_generator, executor):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=executor, port_monitoring=port1
    ) as f:
        resp = req.get(f'http://localhost:{port1}/')
        assert resp.status_code == 200

        f.post(
            f'/foo', inputs=DocumentArray.empty(size=10), request_size=2
        )  # process 10 documents on foo

        resp = req.get(f'http://localhost:{port1}/')
        assert (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 10.0'  # check that we count 10 documents on foo
            in str(resp.content)
        )

        assert not (
            f'jina_document_processed{{executor="DummyExecutor",executor_endpoint="/bar",runtime_name="executor0/rep-0"}}'  # check that we does not start counting documents on bar as it has not been called yet
            in str(resp.content)
        )

        assert (
            f'jina_number_of_successful_requests_total{{runtime_name="executor0/rep-0"}} 5.0'  # check that 5 requests were successful (10/2=5)
            in str(resp.content)
        )

        f.post(
            f'/bar', inputs=DocumentArray.empty(size=5), request_size=1
        )  # process 5 documents on bar

        resp = req.get(f'http://localhost:{port1}/')

        assert (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/bar",runtime_name="executor0/rep-0"}} 5.0'  # check that we count 5 documents on bar
            in str(resp.content)
        )

        assert (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 10.0'  # check that nothing change on foo count
            in str(resp.content)
        )

        assert (
            f'jina_number_of_successful_requests_total{{runtime_name="executor0/rep-0"}} 10.0'  # check that 7 requests were successful so far (5/1 + 5 = 10)
            in str(resp.content)
        )


def test_disable_monitoring_on_pods(port_generator, executor):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=executor,
        port_monitoring=port1,
        monitoring=False,
    ):
        with pytest.raises(req.exceptions.ConnectionError):  # disable on port1
            _ = req.get(f'http://localhost:{port1}/')

        resp = req.get(f'http://localhost:{port0}/')  # enable on port0
        assert resp.status_code == 200


def test_disable_monitoring_on_gatway_only(port_generator, executor):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=False, port_monitoring=port0).add(
        uses=executor,
        port_monitoring=port1,
        monitoring=True,
    ):
        with pytest.raises(req.exceptions.ConnectionError):  # disable on port1
            _ = req.get(f'http://localhost:{port0}/')

        resp = req.get(f'http://localhost:{port1}/')  # enable on port0
        assert resp.status_code == 200


def test_requests_size(port_generator, executor):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=executor, port_monitoring=port1
    ) as f:
        f.post('/foo', inputs=DocumentArray.empty(size=1))

        resp = req.get(f'http://localhost:{port1}/')  # enable on port0
        assert resp.status_code == 200

        assert (
            f'jina_request_size_bytes_count{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )

        def _get_request_bytes_size():
            resp = req.get(f'http://localhost:{port1}/')  # enable on port0

            resp_lines = str(resp.content).split('\\n')
            byte_line = [
                line
                for line in resp_lines
                if 'jina_request_size_bytes_sum{executor="DummyExecutor"' in line
            ]

            return float(byte_line[0][-5:])

        measured_request_bytes_sum_init = _get_request_bytes_size()
        f.post('/foo', inputs=DocumentArray.empty(size=1))
        measured_request_bytes_sum = _get_request_bytes_size()

        assert measured_request_bytes_sum > measured_request_bytes_sum_init


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
    runtime_name = (
        'gateway/rep-0/GRPCGatewayRuntime' if protocol == 'grpc' else 'gateway/rep-0'
    )

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

        p_send = multiprocessing.Process(target=_send_request)
        _assert_pending_value('0.0', runtime_name, port0)

        p_send.start()
        time.sleep(1)

        _assert_pending_value('1.0', runtime_name, port0)

        p_send.join()
        assert p_send.exitcode == 0
        _assert_pending_value('0.0', runtime_name, port0)


def _create_worker_runtime(port, name='', executor=None):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(
    graph_description, pod_addresses, port, port_monitoring, protocol='grpc', retries=-1
):
    if protocol == 'http':
        gateway_runtime = HTTPGatewayRuntime
    elif protocol == 'websocket':
        gateway_runtime = WebSocketGatewayRuntime
    else:
        gateway_runtime = GRPCGatewayRuntime
    with gateway_runtime(
        set_gateway_parser().parse_args(
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
            ]
        )
    ) as runtime:
        runtime.run_forever()


def _create_worker(port):
    # create a single worker runtime
    p = multiprocessing.Process(target=_create_worker_runtime, args=(port,))
    p.start()
    time.sleep(0.1)
    return p


def _create_gateway(port, port_monitoring, graph, pod_addr, protocol, retries=-1):
    # create a single worker runtime
    # create a single gateway runtime
    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph, pod_addr, port, port_monitoring, protocol, retries),
    )
    p.start()
    time.sleep(0.1)
    return p


def _send_request(gateway_port, protocol):
    """send request to gateway and see what happens"""
    from jina.clients import Client

    c = Client(host='localhost', port=gateway_port, protocol=protocol)
    return c.post(
        '/foo',
        inputs=[Document(text='hi') for _ in range(2)],
        request_size=1,
        return_responses=True,
        continue_on_error=True,
    )


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_pending_requests_with_connection_error(port_generator, protocol):
    runtime_name = 'gateway/GRPCGatewayRuntime' if protocol == 'grpc' else 'gateway'
    gateway_port = port_generator()
    worker_port = port_generator()
    port_monitoring = port_generator()
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    gateway_process = _create_gateway(
        gateway_port, port_monitoring, graph_description, pod_addresses, protocol
    )

    time.sleep(1.0)

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{gateway_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    try:
        p = multiprocessing.Process(target=_send_request, args=(gateway_port, protocol))
        p.start()
        p.join()
        time.sleep(2)
        _assert_pending_value('0.0', runtime_name, port_monitoring)
    except Exception:
        assert False
    finally:  # clean up runtimes
        gateway_process.terminate()
        gateway_process.join()


def test_failed_successful_request_count(port_generator, failing_executor):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=failing_executor, port_monitoring=port1
    ) as f:
        resp = req.get(f'http://localhost:{port1}/')
        assert resp.status_code == 200

        f.post(
            '/fail',
            inputs=DocumentArray.empty(size=10),
            request_size=1,
            continue_on_error=True,
        )  # send 10 requests, 5 should fail and 5 should succeed

        resp = req.get(f'http://localhost:{port1}/')

        assert (
            f'jina_number_of_successful_requests_total{{runtime_name="executor0/rep-0"}} 5.0'
            in str(resp.content)
        )

        assert (
            f'jina_number_of_failed_requests_total{{runtime_name="executor0/rep-0"}} 5.0'
            in str(resp.content)
        )

        resp = req.get(f'http://localhost:{port0}/')

        assert (
            f'jina_number_of_successful_requests_total{{runtime_name="gateway/rep-0/GRPCGatewayRuntime"}} 5.0'
            in str(resp.content)
        )

        assert (
            f'jina_number_of_failed_requests_total{{runtime_name="gateway/rep-0/GRPCGatewayRuntime"}} 5.0'
            in str(resp.content)
        )


def test_timeout_send(port_generator, failing_executor):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0, timeout_send=1).add(
        uses=failing_executor, port_monitoring=port1
    ) as f:
        resp = req.get(f'http://localhost:{port1}/')
        assert resp.status_code == 200

        # try sending Document, this should timeout
        try:
            f.post('/timeout', inputs=DocumentArray.empty(size=1))
        # ignore timeout
        except ConnectionError:
            pass

        # test that timeout was detected in gateway
        resp = req.get(f'http://localhost:{port0}/')

        assert (
            f'jina_number_of_successful_requests_total{{runtime_name="gateway/rep-0/GRPCGatewayRuntime"}} 0.0'
            in str(resp.content)
        )

        assert (
            f'jina_number_of_failed_requests_total{{runtime_name="gateway/rep-0/GRPCGatewayRuntime"}} 1.0'
            in str(resp.content)
        )
