from http import HTTPStatus
from pytest_kind import cluster
from pykube import Pod

# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
# TODO don't use pytest-kind anymore
cluster.KIND_VERSION = 'v0.11.1'
import pytest
import requests
import multiprocessing
import time

from jina import Flow
from jina.peapods.pods.k8slib.kubernetes_tools import (
    get_port_forward_contextmanager,
    K8sClients,
)


def run_test(flow, logger, k8s_cluster, app_names, endpoint, port_expose):
    event = multiprocessing.Event()
    watch_process = multiprocessing.Process(
        target=watch_pods,
        kwargs={'k8s_cluster': k8s_cluster, 'app_names': app_names, 'event': event},
        daemon=True,
    )
    watch_process.start()
    with flow:
        resp = send_dummy_request(endpoint, flow, logger, port_expose=port_expose)
        event.set()
    watch_process.join()
    watch_process.terminate()
    return resp


def watch_pods(k8s_cluster, flow_name, app_names, event):
    # using Pykube to query pods
    client = K8sClients()
    client.core_v1.list_names
    while not event.is_set():
        for app in app_names:
            logs = k8s_cluster.kubectl([f'get pods -n {flow_name}'])


def send_dummy_request(endpoint, flow, logger, port_expose):
    logger.debug(f'Starting port-forwarding to gateway service...')
    with get_port_forward_contextmanager(
        namespace=flow.args.name, port_expose=port_expose
    ):
        logger.debug(f'Port-forward running...')
        resp = requests.post(
            f'http://localhost:{port_expose}/{endpoint}',
            json={'data': [{} for _ in range(10)]},
        )
    return resp


@pytest.fixture()
def k8s_flow_with_init_container(
    test_executor_image: str, executor_merger_image: str, dummy_dumper_image: str
) -> Flow:
    flow = Flow(
        name='test-flow-with-init-container',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
    ).add(
        name='test_executor',
        uses=test_executor_image,
        k8s_init_container_command=["python", "dump.py", "/shared/test_file.txt"],
        k8s_uses_init=dummy_dumper_image,
        k8s_mount_path='/shared',
        timeout_ready=120000,
    )
    return flow


@pytest.fixture()
def k8s_flow_with_sharding(
    test_executor_image: str, executor_merger_image: str, dummy_dumper_image: str
) -> Flow:
    flow = Flow(
        name='test-flow-with-sharding',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
    ).add(
        name='test_executor',
        shards=2,
        replicas=2,
        uses=test_executor_image,
        uses_after=executor_merger_image,
        timeout_ready=360000,
    )
    return flow


@pytest.mark.timeout(3600)
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
def test_flow_with_needs(
    k8s_cluster,
    test_executor_image: str,
    executor_merger_image: str,
    load_images_in_kind,
    set_test_pip_version,
    logger,
    k8s_connection_pool: bool,
):
    name = 'test-flow-with-needs'
    if k8s_connection_pool:
        name += '-pool'
    flow = (
        Flow(
            name=name,
            port_expose=9090,
            infrastructure='K8S',
            protocol='http',
            timeout_ready=120000,
            k8s_connection_pool=k8s_connection_pool,
        )
        .add(
            name='segmenter',
            uses=test_executor_image,
            timeout_ready=120000,
        )
        .add(
            name='textencoder',
            uses=test_executor_image,
            needs='segmenter',
            timeout_ready=120000,
        )
        .add(
            name='imageencoder',
            uses=test_executor_image,
            needs='segmenter',
            timeout_ready=120000,
        )
        .add(
            name='merger',
            uses=executor_merger_image,
            timeout_ready=120000,
            needs=['imageencoder', 'textencoder'],
        )
    )
    resp = run_test(
        flow,
        logger,
        k8s_cluster,
        app_names=['segmenter', 'gateway', 'imageencoder', 'textencoder'],
        endpoint='index',
        port_expose=9090,
    )

    expected_traversed_executors = {
        'segmenter',
        'imageencoder',
        'textencoder',
    }

    assert resp.status_code == HTTPStatus.OK
    docs = resp.json()['data']['docs']
    assert len(docs) == 10
    for doc in docs:
        assert set(doc['tags']['traversed-executors']) == expected_traversed_executors


@pytest.mark.timeout(3600)
def test_flow_with_init(
    k8s_cluster,
    k8s_flow_with_init_container: Flow,
    load_images_in_kind,
    set_test_pip_version,
    logger,
):
    resp = run_test(
        k8s_flow_with_init_container,
        logger,
        k8s_cluster,
        app_names=['test-executor', 'gateway'],
        endpoint='search',
        port_expose=9090,
    )

    assert resp.status_code == HTTPStatus.OK
    docs = resp.json()['data']['docs']
    assert len(docs) == 10
    for doc in docs:
        assert doc['tags']['file'] == ['1\n', '2\n', '3']


@pytest.mark.timeout(3600)
def test_flow_with_sharding(
    k8s_cluster,
    k8s_flow_with_sharding: Flow,
    load_images_in_kind,
    set_test_pip_version,
    logger,
):
    resp = run_test(
        k8s_flow_with_sharding,
        logger,
        k8s_cluster,
        app_names=[
            'test-executor-head',
            'test-executor-tail',
            'test-executor-0',
            'test-executor-1',
            'gateway',
        ],
        endpoint='index',
        port_expose=9090,
    )

    expected_traversed_executors = {
        'test_executor',
    }

    assert resp.status_code == HTTPStatus.OK
    docs = resp.json()['data']['docs']
    assert len(docs) == 10
    for doc in docs:
        assert set(doc['tags']['traversed-executors']) == expected_traversed_executors
