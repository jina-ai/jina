import multiprocessing
import time

import pytest
import requests as req
from docarray import DocumentArray

from jina import Executor, Flow, requests


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


def test_monitoring_head(port_generator, executor):
    port1 = port_generator()
    port2 = port_generator()

    with Flow(monitoring=True, port_monitoring=port_generator()).add(
        uses=executor, port_monitoring=port1
    ).add(uses=executor, port_monitoring=port2, shards=2) as f:

        port3 = f._deployment_nodes['executor0'].pod_args['pods'][0][0].port_monitoring
        port4 = f._deployment_nodes['executor1'].pod_args['pods'][0][0].port_monitoring

        for port in [port1, port2, port3, port4]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port2}/')
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
            f'/foo', inputs=DocumentArray.empty(size=4)
        )  # process 4 documents on foo

        resp = req.get(f'http://localhost:{port1}/')
        assert (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 4.0'  # check that we count 4 documents on foo
            in str(resp.content)
        )

        assert not (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/bar",runtime_name="executor0/rep-0"}}'  # check that we does not start counting documents on bar as it has not been called yet
            in str(resp.content)
        )

        f.post(
            f'/bar', inputs=DocumentArray.empty(size=5)
        )  # process 5 documents on bar

        assert not (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/bar",runtime_name="executor0/rep-0"}} 5.0'  # check that we count 5 documents on foo
            in str(resp.content)
        )

        assert (
            f'jina_document_processed_total{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 4.0'  # check that we nothing change on bar count
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
            resp = req.get(f'http://localhost:{port1}/')

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
            resp = req.get(f'http://localhost:{port0}/')

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


def test_pending_request(port_generator):
    port0 = port_generator()
    port1 = port_generator()

    class SlowExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            time.sleep(5)

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=SlowExecutor, port_monitoring=port1
    ) as f:

        def _send_request():
            f.search(inputs=DocumentArray.empty(size=1))

        def _assert_pending_value(val: str):
            resp = req.get(f'http://localhost:{port0}/')
            assert resp.status_code == 200
            assert (
                f'jina_number_of_pending_requests{{runtime_name="gateway/rep-0/GRPCGatewayRuntime"}} {val}'
                in str(resp.content)
            )

        _assert_while = lambda: _assert_pending_value(
            '1.0'
        )  # while the request is being processed the counter is at one
        _assert_after = lambda: _assert_pending_value(
            '0.0'
        )  # but before and after it is at 0
        _assert_before = lambda: _assert_pending_value(
            '0.0'
        )  # but before and after it is at 0

        p_send = multiprocessing.Process(target=_send_request)
        p_before = multiprocessing.Process(target=_assert_before)
        p_while = multiprocessing.Process(target=_assert_while)

        p_before.start()
        time.sleep(1)
        p_send.start()
        time.sleep(1)
        p_while.start()

        for p in [p_before, p_send, p_while]:
            p.join()

        exitcodes = []
        for p in [p_before, p_send, p_while]:
            p.terminate()
            exitcodes.append(
                p.exitcode
            )  # collect the exit codes and assert after all of them have been terminated, to avoid timeouts

        for code in exitcodes:
            assert not code

        _assert_after()
