import pytest
import requests as req
from docarray import DocumentArray

from jina import Executor, Flow, requests

from . import get_metric_values


@pytest.fixture()
def executor():
    class DummyExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs): ...

        @requests(on='/bar')
        def bar(self, docs, **kwargs): ...

    return DummyExecutor


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
            f'jina_received_request_bytes_count{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )

        assert (
            f'jina_sent_response_bytes_count{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )

        def _get_request_bytes_size():
            resp = req.get(f'http://localhost:{port1}/').content.decode()
            metrics = get_metric_values(resp)

            measured_request_bytes_sum = metrics[
                'jina_received_request_bytes_sum{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}'
            ]
            measured_request_bytes_send_sum = metrics[
                'jina_sent_response_bytes_sum{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}'
            ]

            return measured_request_bytes_sum, measured_request_bytes_send_sum

        (
            measured_request_bytes_sum_init,
            measured_request_bytes_send_sum_init,
        ) = _get_request_bytes_size()
        f.post('/foo', inputs=DocumentArray.empty(1))
        (
            measured_request_bytes_sum,
            measured_request_bytes_send_sum,
        ) = _get_request_bytes_size()

        assert measured_request_bytes_sum > measured_request_bytes_sum_init
        assert measured_request_bytes_send_sum > measured_request_bytes_send_sum_init


def test_request_size_increasing(port_generator, executor):
    class IncreaseSizeExecutor(executor):
        @requests
        def foo(self, docs, **kwargs):
            for doc_ in docs:
                doc_.text = 'hello wolrd' * 10_000

    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=IncreaseSizeExecutor, port_monitoring=port1
    ) as f:
        f.post('/', inputs=DocumentArray.empty(size=1))

        raw_metrics_executor = req.get(f'http://localhost:{port1}/').content.decode()
        raw_metrics_gateway = req.get(f'http://localhost:{port0}/').content.decode()

    metrics_executor = get_metric_values(raw_metrics_executor)
    metrics_gateway = get_metric_values(raw_metrics_gateway)

    size_received_at_executor = metrics_executor[
        'jina_received_request_bytes_sum{executor="IncreaseSizeExecutor",executor_endpoint="/",runtime_name="executor0/rep-0"}'
    ]
    size_send_by_gateway = metrics_gateway[
        'jina_sent_request_bytes_sum{runtime_name="gateway/rep-0"}'
    ]
    size_return_from_exec_at_gateway = metrics_gateway[
        'jina_received_response_bytes_sum{runtime_name="gateway/rep-0"}'
    ]
    size_received_at_gateway = metrics_gateway[
        'jina_received_request_bytes_sum{runtime_name="gateway/rep-0"}'
    ]
    size_send_by_executor = metrics_executor[
        'jina_sent_response_bytes_sum{executor="IncreaseSizeExecutor",executor_endpoint="/",runtime_name="executor0/rep-0"}'
    ]

    size_return_to_the_client = metrics_gateway[
        'jina_sent_response_bytes_sum{runtime_name="gateway/rep-0"}'
    ]

    assert size_received_at_gateway > 0

    assert size_send_by_gateway > 0

    assert (
        size_send_by_gateway == size_received_at_executor
    )  # both should have the same size since it is just the same request send from gateway to executor

    assert (
        size_received_at_executor < 10 * size_return_from_exec_at_gateway
    )  # the return request should be way bigger since we add data

    assert (
        size_return_from_exec_at_gateway == size_send_by_executor
    )  # both should have the same size since it is just the same request send from executor to gateway

    assert size_return_to_the_client > 0

    assert size_return_from_exec_at_gateway > 0


def test_deprecated_metric_byte_size(executor, port_generator):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=executor, port_monitoring=port1
    ) as f:
        f.post('/foo', inputs=DocumentArray.empty(size=1))

        raw_metrics_executor = req.get(f'http://localhost:{port1}/').content.decode()
        raw_metrics_gateway = req.get(f'http://localhost:{port0}/').content.decode()

    metrics_executor = get_metric_values(raw_metrics_executor)
    metrics_gateway = get_metric_values(raw_metrics_gateway)

    assert (
        metrics_gateway['jina_request_size_bytes_sum{runtime_name="gateway/rep-0"}']
        == metrics_gateway[
            'jina_received_request_bytes_sum{runtime_name="gateway/rep-0"}'
        ]
    )
    assert (
        metrics_executor[
            'jina_request_size_bytes_sum{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}'
        ]
        == metrics_executor[
            'jina_received_request_bytes_sum{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}'
        ]
    )
