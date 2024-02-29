import time

import pytest
import requests as req
from docarray import DocumentArray

from jina import Executor, Flow, requests


@pytest.fixture()
def executor():
    class DummyExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs): ...

        @requests(on='/bar')
        def bar(self, docs, **kwargs): ...

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
            assert f'jina_successful_requests_total' in str(resp.content)
            assert f'jina_failed_requests_total' in str(resp.content)


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
        assert f'jina_successful_requests_total' in str(resp.content)
        assert f'jina_failed_requests_total' in str(resp.content)
        assert f'jina_received_response_bytes' in str(resp.content)
        assert f'jina_sent_request_bytes' in str(resp.content)
        assert f'jina_received_request_bytes' in str(resp.content)
        assert f'jina_sent_response_bytes' in str(resp.content)


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
        assert f'jina_received_response_bytes' in str(resp.content)
        assert f'jina_sent_request_bytes' in str(resp.content)


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


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http', None])
def test_monitoring_replicas_and_shards(port_generator, executor, protocol):
    n_shards = 2
    n_replicas = 3
    port_shards_list = [port_generator() for _ in range(n_shards * n_replicas)]
    port_head = port_generator()
    port_monitoring = ','.join([str(port) for port in [port_head] + port_shards_list])
    port1 = port_generator()

    flow = (
        Flow(protocol=protocol, monitoring=True, port_monitoring=port1)
        if protocol
        else Flow(monitoring=True, port_monitoring=port1)
    )

    f = flow.add(
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
            assert f'jina_successful_requests_total' in str(resp.content)
            assert f'jina_failed_requests_total' in str(resp.content)

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
            f'jina_successful_requests_total{{runtime_name="executor0/rep-0"}} 5.0'  # check that 5 requests were successful (10/2=5)
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
            f'jina_successful_requests_total{{runtime_name="executor0/rep-0"}} 10.0'  # check that 7 requests were successful so far (5/1 + 5 = 10)
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
            f'jina_successful_requests_total{{runtime_name="executor0/rep-0"}} 5.0'
            in str(resp.content)
        )

        assert (
            f'jina_failed_requests_total{{runtime_name="executor0/rep-0"}} 5.0'
            in str(resp.content)
        )

        resp = req.get(f'http://localhost:{port0}/')

        assert (
            f'jina_successful_requests_total{{runtime_name="gateway/rep-0"}} 5.0'
            in str(resp.content)
        )

        assert f'jina_failed_requests_total{{runtime_name="gateway/rep-0"}} 5.0' in str(
            resp.content
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
            f'jina_successful_requests_total{{runtime_name="gateway/rep-0"}} 0.0'
            in str(resp.content)
        )

        assert f'jina_failed_requests_total{{runtime_name="gateway/rep-0"}} 1.0' in str(
            resp.content
        )
