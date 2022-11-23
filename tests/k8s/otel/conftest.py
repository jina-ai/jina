import pytest
import os

from tests.k8s.kind_wrapper import KindClusterWrapper


@pytest.fixture(scope='session')
def otel_test_namespace(k8s_cluster: KindClusterWrapper) -> str:
    """
    Returns a namespace with the otlp-collector, jaeger and prometheus services deployed.

    Service endpoints:
        - otlp-collector:4317 - OTLP GRPC metrics endpoint
        - jaeger:16686 - API endpoint
        - jaeger:4317 - OTLP GRPC tracing endpoint
        - prometheus:9090 - API endpoint
        - otlphttp-mirror - OTLP HTTP metrics endpoint
    Nice for development and debugging:
        - jaeger:16686 - UI endpoint
        - prometheus:9090 - UI endpoint
        - grafana:3000 - UI endpoint
    Returns:
        The namespace name
    """
    NAMESPACE = 'otel-test'
    ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), NAMESPACE)
    k8s_cluster.deploy_from_dir(dir=ARTIFACT_DIR, namespace=NAMESPACE)
    return NAMESPACE
