import time
from pytest_kind import cluster

# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
# TODO don't use pytest-kind anymore

cluster.KIND_VERSION = 'v0.11.1'
import pytest

from jina import Flow, Document


@pytest.fixture()
def k8s_flow_with_needs(test_executor_image: str, executor_merger_image: str) -> Flow:
    flow = (
        Flow(name='test-flow', port_expose=9090, infrastructure='K8S', protocol='http')
        .add(
            name='segmenter',
            uses=test_executor_image,
        )
        .add(
            name='textencoder',
            uses=test_executor_image,
            needs='segmenter',
        )
        .add(
            name='textstorage',
            uses=test_executor_image,
            needs='textencoder',
        )
        .add(
            name='imageencoder',
            uses=test_executor_image,
            needs='segmenter',
        )
        .add(
            name='imagestorage',
            uses=test_executor_image,
            needs='imageencoder',
        )
        .add(
            name='merger',
            uses=executor_merger_image,
            needs=['imagestorage', 'textstorage'],
        )
    )
    return flow


def pull_images(images, cluster, logger):
    # image pull anyways must be Never or IfNotPresent otherwise kubernetes will try to pull the image anyway
    logger.debug(f'Loading docker image into kind cluster...')
    for image in images:
        cluster.needs_docker_image(image)
    # cluster.needs_docker_image('jinaai/jina:test-pip')
    logger.debug(f'Done loading docker image into kind cluster...')


def run_test(images, cluster, flow, logger, endpoint):
    pull_images(images, cluster, logger)
    with flow:
        resp = flow.post(endpoint, [Document() for _ in range(10)], return_results=True)
    return resp


@pytest.fixture()
def k8s_flow_with_init_container(
    test_executor_image: str, executor_merger_image: str, dummy_dumper_image: str
) -> Flow:
    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(
        name='test_executor',
        uses=test_executor_image,
        k8s_init_container_command=["python", "dump.py", "/shared/test_file.txt"],
        k8s_uses_init=dummy_dumper_image,
        k8s_mount_path='/shared',
    )
    return flow


@pytest.fixture()
def k8s_flow_with_sharding(
    test_executor_image: str, executor_merger_image: str, dummy_dumper_image: str
) -> Flow:
    flow = Flow(
        name='test-flow', port_expose=8080, infrastructure='K8S', protocol='http'
    ).add(
        name='test_executor',
        shards=3,
        replicas=2,
        uses=test_executor_image,
        uses_after=executor_merger_image,
    )
    return flow


@pytest.mark.timeout(3600)
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
def test_flow_with_needs(
    k8s_cluster_namespaced,
    test_executor_image,
    executor_merger_image,
    k8s_flow_with_needs: Flow,
    logger,
    k8s_connection_pool: bool,
):
    k8s_flow_with_needs.args.k8s_connection_pool = k8s_connection_pool
    resp = run_test(
        [test_executor_image, executor_merger_image],
        k8s_cluster_namespaced,
        k8s_flow_with_needs,
        logger,
        endpoint='/index',
    )

    expected_traversed_executors = {
        'segmenter',
        'imageencoder',
        'textencoder',
        'imagestorage',
        'textstorage',
    }

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert set(doc.tags['traversed-executors']) == expected_traversed_executors


@pytest.mark.timeout(3600)
def test_flow_with_init(
    k8s_cluster_namespaced,
    test_executor_image,
    dummy_dumper_image: str,
    k8s_flow_with_init_container: Flow,
    logger,
):
    resp = run_test(
        [test_executor_image, dummy_dumper_image],
        k8s_cluster_namespaced,
        k8s_flow_with_init_container,
        logger,
        endpoint='/search',
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['file'] == ['1\n', '2\n', '3']


@pytest.mark.timeout(3600)
def test_flow_with_sharding(
    k8s_cluster_namespaced,
    test_executor_image,
    executor_merger_image,
    k8s_flow_with_sharding: Flow,
    logger,
):
    resp = run_test(
        [test_executor_image, executor_merger_image],
        k8s_cluster_namespaced,
        k8s_flow_with_sharding,
        logger,
        endpoint='/index',
    )

    expected_traversed_executors = {
        'test_executor',
    }

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert set(doc.tags['traversed-executors']) == expected_traversed_executors
