import time

from jina import Flow
from tests.integration.instrumentation import (
    get_exported_jobs,
    get_flow_metric_labels,
    get_services,
)


def test_docker_instrumentation(
    jaeger_port,
    otlp_collector,
    otlp_receiver_port,
    docker_image_name,
    docker_image_built,
    prometheus_client,
    expected_flow_metric_labels,
):
    f = Flow(
        tracing=True,
        traces_exporter_host='http://localhost',
        traces_exporter_port=otlp_receiver_port,
        metrics=True,
        metrics_exporter_host='http://localhost',
        metrics_exporter_port=otlp_receiver_port,
    ).add(uses=f'docker://{docker_image_name}')

    with f:
        from docarray import DocumentArray

        f.post(f'/search', DocumentArray.empty(), continue_on_error=True)
        # give some time for the tracing and metrics exporters to finish exporting.
        # the client is slow to export the data
        time.sleep(3)

    services = get_services(jaeger_port)
    assert set(services) == {'executor0/rep-0', 'gateway/rep-0'}

    exported_jobs = get_exported_jobs(prometheus_client)
    assert exported_jobs == {
        'gateway/rep-0',
        'executor0/rep-0',
    }

    flow_metric_labels = get_flow_metric_labels(prometheus_client)
    assert flow_metric_labels.issubset(expected_flow_metric_labels)
