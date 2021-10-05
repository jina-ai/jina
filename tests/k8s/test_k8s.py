from http import HTTPStatus
from pytest_kind import cluster

# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
# TODO don't use pytest-kind anymore
cluster.KIND_VERSION = 'v0.11.1'
import pytest
import requests
import multiprocessing
import threading
import time

from jina import Flow
from jina.peapods.pods.k8slib.kubernetes_tools import (
    get_port_forward_contextmanager,
    K8sClients,
)


def run_test(flow, logger, app_names, endpoint, port_expose, watch_pods=False):
    if watch_pods:
        event = multiprocessing.Event()

        watch_process = multiprocessing.Process(
            target=_watch_pods,
            kwargs={
                'flow_name': flow.args.name,
                'app_names': app_names,
                'event': event,
            },
            daemon=True,
        )
        watch_process.start()
    with flow:
        if watch_pods:
            event.is_set()
        resp = send_dummy_request(endpoint, flow, logger, port_expose=port_expose)
    if watch_pods:
        event.set()
        watch_process.terminate()
    return resp


def _tail_logs(name, flow_name, pod_name):
    from jina.logging.logger import JinaLogger
    from kubernetes.watch import Watch

    logger = JinaLogger(f'{flow_name}-{name}:{pod_name}')
    logger.debug(f'\n\n ==== TAILING LOGS FOR APP {name} and pod {pod_name} === \n\n')
    k8s_client = K8sClients()

    def _work():
        try:
            logger.debug(f' Try to watch now')
            w = Watch()
            for e in w.stream(
                k8s_client.core_v1.read_namespaced_pod_log,
                name=pod_name,
                namespace=flow_name,
            ):
                logger.info(e)
        except Exception as ex:
            logger.debug(f' exception {ex}')
            time.sleep(0.5)

    while True:
        with logger:
            _work()
        time.sleep(0.5)


def _watch_pods(flow_name, app_names, event):
    # using Pykube to query pods
    from jina.logging.logger import JinaLogger

    logger = JinaLogger(f'test_watch_cluster-{flow_name}')
    k8s_client = K8sClients()
    added_apps = []
    import time

    now = time.time_ns()
    timeout_ns = 1000000000 * 240
    spawn_new_threads = True
    while (
        not event.is_set() and time.time_ns() - now < timeout_ns and spawn_new_threads
    ):
        with logger:
            logger.info(
                f' Wants to watch pods for the following deployments {app_names}'
            )
            try:
                threads = []
                for app in app_names:
                    if app not in added_apps:
                        pods = k8s_client.core_v1.list_namespaced_pod(
                            namespace=flow_name, label_selector=f'app={app}'
                        )
                        pod_names = [item.metadata.name for item in pods.items]
                        logger.debug(
                            f'\n\n == Found {pod_names} for app {app} === \n\n'
                        )
                        for i, pod_name in enumerate(pod_names):
                            th = threading.Thread(
                                target=_tail_logs,
                                kwargs={
                                    'name': f'replica-{i}',
                                    'flow_name': flow_name,
                                    'pod_name': pod_name,
                                },
                                daemon=True,
                            )
                            th.start()
                            threads.append(th)
                        if len(pod_names) > 0:
                            added_apps.append(app)
                if len(added_apps) == len(app_names):
                    spawn_new_threads = False
            except Exception:
                print(f' Exception Here Joan')
                pass
            finally:
                time.sleep(0.5)

    event.wait(timeout=timeout_ns / 1000)
    # print(f' Join log threads')
    # for thread in threads:
    #     thread.join()


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
        watch_pods=True,
        app_names=['gateway', 'segmenter', 'imageencoder', 'textencoder'],
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
        watch_pods=True,
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
        watch_pods=True,
        app_names=[
            'gateway',
            'test-executor-head',
            'test-executor-0',
            'test-executor-1',
            'test-executor-tail',
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
