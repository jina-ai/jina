import os
from pathlib import Path

import pytest
from pytest_kind import KindCluster, cluster

from jina.logging.logger import JinaLogger
from tests.k8s_otel.kind_wrapper import KindClusterWrapperV2

# The default version broke cni at some point. That's why we need to specify the version here.
# This can and probably should be put in env variable actually.
cluster.KIND_VERSION = 'v0.11.1'

# TODO: Can we get jina image to build here as well?
@pytest.fixture(scope='session', autouse=True)
def build_and_load_images(k8s_cluster_v2: KindClusterWrapperV2) -> None:
    CUR_DIR = Path(__file__).parent
    k8s_cluster_v2.build_and_load_docker_image(
        str(CUR_DIR / 'test-instrumentation'), 'test-instrumentation', 'test-pip'
    )
    k8s_cluster_v2.load_docker_image(image_name='jinaai/jina', tag='test-pip')
    os.environ['JINA_GATEWAY_IMAGE'] = 'jinaai/jina:test-pip'
    yield
    del os.environ['JINA_GATEWAY_IMAGE']
    k8s_cluster_v2.remove_docker_image('test-instrumentation', 'test-pip')


@pytest.fixture(scope='session')
def k8s_cluster_v2(kind_cluster: KindCluster) -> KindClusterWrapperV2:
    return KindClusterWrapperV2(kind_cluster, JinaLogger('kubernetes-cluster-logger'))


@pytest.fixture(scope='session')
def otel_test_namespace(k8s_cluster_v2: KindClusterWrapperV2) -> str:
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
    k8s_cluster_v2.deploy_from_dir(dir=ARTIFACT_DIR, namespace=NAMESPACE)
    return NAMESPACE
