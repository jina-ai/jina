import time

import requests as req
from prometheus_client import CollectorRegistry, start_http_server

from jina.serve.monitoring import _SummaryDeprecated

from . import get_metric_values


def test_deprecated_summary_observe(port_generator):

    metrics_registry = CollectorRegistry()

    port = port_generator()
    start_http_server(port, registry=metrics_registry)

    metric = _SummaryDeprecated(
        old_name='old',
        name='new',
        documentation='New',
        namespace='jina',
        registry=metrics_registry,
    )

    metric.observe(1.0)

    metric_parsed = get_metric_values(
        req.get(f'http://localhost:{port}/').content.decode()
    )

    assert metric_parsed['jina_new_sum'] == metric_parsed['jina_old_sum']
    assert metric_parsed['jina_new_created'] == metric_parsed['jina_old_created']
    assert metric_parsed['jina_new_count'] == metric_parsed['jina_old_count']


def test_deprecated_summary_timing(port_generator):

    metrics_registry = CollectorRegistry()

    port = port_generator()
    start_http_server(port, registry=metrics_registry)

    metric = _SummaryDeprecated(
        old_name='old',
        name='new',
        documentation='New',
        namespace='jina',
        registry=metrics_registry,
    )

    with metric.time():
        time.sleep(0.1)

    metric_parsed = get_metric_values(
        req.get(f'http://localhost:{port}/').content.decode()
    )

    assert metric_parsed['jina_new_sum'] == metric_parsed['jina_old_sum']
    assert metric_parsed['jina_new_created'] == metric_parsed['jina_old_created']
    assert metric_parsed['jina_new_count'] == metric_parsed['jina_old_count']


def test_deprecated_summary_labels(port_generator):

    metrics_registry = CollectorRegistry()

    port = port_generator()
    start_http_server(port, registry=metrics_registry)

    metric = _SummaryDeprecated(
        old_name='old',
        name='new',
        documentation='New',
        namespace='jina',
        registry=metrics_registry,
        labelnames=('A',),
    ).labels('a')

    metric.observe(1)

    metric_parsed = get_metric_values(
        req.get(f'http://localhost:{port}/').content.decode()
    )

    assert metric_parsed['jina_new_sum{A="a"}'] == metric_parsed['jina_old_sum{A="a"}']
    assert (
        metric_parsed['jina_new_created{A="a"}']
        == metric_parsed['jina_old_created{A="a"}']
    )
    assert (
        metric_parsed['jina_new_count{A="a"}'] == metric_parsed['jina_old_count{A="a"}']
    )
