from typing import Dict, List

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

        assert (
            f'jina_send_request_bytes_count{{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )

        def _get_request_bytes_size():
            resp = req.get(f'http://localhost:{port1}/').content.decode()
            metrics = get_metric_values(resp)

            measured_request_bytes_sum = metrics[
                'jina_request_size_bytes_sum{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}'
            ]
            measured_request_bytes_send_sum = metrics[
                'jina_send_request_bytes_sum{executor="DummyExecutor",executor_endpoint="/foo",runtime_name="executor0/rep-0"}'
            ]

            return measured_request_bytes_sum, measured_request_bytes_send_sum

        (
            measured_request_bytes_sum_init,
            measured_request_bytes_send_sum_init,
        ) = _get_request_bytes_size()
        f.post('/foo', inputs=DocumentArray.empty(size=1))
        (
            measured_request_bytes_sum,
            measured_request_bytes_send_sum,
        ) = _get_request_bytes_size()

        assert measured_request_bytes_sum > measured_request_bytes_sum_init
        assert measured_request_bytes_send_sum > measured_request_bytes_send_sum_init


def get_metric_values(raw_metrics: str) -> Dict[str, float]:
    """
    get the value of a metric from the prometheus endpoint
    :param raw_metrics: raw string coming from scrapping the http prometheus endpoint
    :return: Dictionary which full metrics name as key and the corresponding value
    """
    metrics = dict()

    for line in raw_metrics.split('\n'):
        if not line.startswith('#') and ' ' in line:
            line_split = line.split(' ')

            metric_name = ''.join(line_split[0:-1])

            metric_value = float(line_split[-1])

            metrics[metric_name] = metric_value

    return metrics
