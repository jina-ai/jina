import os
import time

import pytest
from prometheus_api_client import PrometheusConnect


@pytest.fixture()
def otlp_collector():
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
def prometheus_client(otlp_collector):
    return PrometheusConnect(url='http://localhost:9090', disable_ssl=True)


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
    ]
