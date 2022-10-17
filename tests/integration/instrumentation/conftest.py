import os
import time

import pytest
from prometheus_api_client import PrometheusConnect

from jina.helper import random_port


@pytest.fixture()
def jaeger_port():
    port = random_port()
    os.environ['JAEGER_PORT'] = str(port)
    yield port
    del os.environ['JAEGER_PORT']


@pytest.fixture()
def prometheus_backend_port():
    port = random_port()
    os.environ['PROMETHEUS_BACKEND_PORT'] = str(port)
    yield port
    del os.environ['PROMETHEUS_BACKEND_PORT']


@pytest.fixture()
def otlp_receiver_port():
    port = random_port()
    os.environ['OTLP_RECEIVER_PORT'] = str(port)
    yield port
    del os.environ['OTLP_RECEIVER_PORT']


@pytest.fixture()
def otlp_collector(jaeger_port, prometheus_backend_port, otlp_receiver_port):
    file_dir = os.path.dirname(__file__)
    os.system(
        f"docker-compose -f {os.path.join(file_dir, 'docker-compose.yml')} up -d --remove-orphans"
    )
    time.sleep(1)
    yield
    os.system(
        f"docker-compose -f {os.path.join(file_dir, 'docker-compose.yml')} down --remove-orphans"
    )


@pytest.fixture()
def prometheus_client(prometheus_backend_port, otlp_collector):
    return PrometheusConnect(
        url=f'http://localhost:{prometheus_backend_port}', disable_ssl=True
    )


@pytest.fixture()
def set_metrics_export_interval():
    os.environ['OTEL_METRIC_EXPORT_INTERVAL'] = '200'  # milliseconds
    yield
    del os.environ['OTEL_METRIC_EXPORT_INTERVAL']


@pytest.fixture()
def instrumented_services_sharded():
    return [
        'gateway/rep-0',
        'executor0/shard-0/rep-0',
        'executor0/shard-1/rep-0',
        'executor0/head',
    ]


@pytest.fixture()
def expected_flow_metric_labels():
    return [
        'number_of_pending_requests',
        'received_request_bytes_bucket',
        'received_request_bytes_count',
        'received_request_bytes_sum',
        'received_response_bytes_bucket',
        'received_response_bytes_count',
        'received_response_bytes_sum',
        'receiving_request_seconds_bucket',
        'receiving_request_seconds_count',
        'receiving_request_seconds_sum',
        'request_counter',  # otel or prometheus related
        'sent_request_bytes_bucket',
        'sent_request_bytes_count',
        'sent_request_bytes_sum',
        'sent_response_bytes_bucket',
        'sent_response_bytes_count',
        'sent_response_bytes_sum',
        'successful_requests',
        'target_info',  # otel or prometheus related
        'up',  # otel or prometheus related
        'failed_requests',
        'document_processed',
        'receiving_request_seconds_bucket',
        'receiving_request_seconds_count',
        'receiving_request_seconds_sum',
        'sending_request_seconds_bucket',
        'sending_request_seconds_count',
        'sending_request_seconds_sum',
        'process_request_seconds_bucket',
        'process_request_seconds_count',
        'process_request_seconds_sum',
        'executor',
        'executor_endpoint',
        'runtime_name',
    ]
