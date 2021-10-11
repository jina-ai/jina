from pytest_kind import cluster

# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
# TODO don't use pytest-kind anymore
cluster.KIND_VERSION = 'v0.11.1'
import pytest

from jina import Flow, Document


def run_test(flow, endpoint, port_expose):
    with flow:
        resp = flow.post(
            endpoint,
            [Document() for _ in range(10)],
            return_results=True,
            port_expose=port_expose,
        )
    return resp


@pytest.fixture()
def k8s_flow_with_init_container(
    test_executor_image: str, dummy_dumper_image: str
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
    test_executor_image: str, executor_merger_image: str
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


@pytest.fixture()
def k8s_flow_configmap(test_executor_image: str) -> Flow:
    flow = Flow(
        name='k8s-flow-configmap',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
    ).add(
        name='test_executor',
        uses=test_executor_image,
        timeout_ready=12000,
        env={'k1': 'v1', 'k2': 'v2'},
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
        endpoint='/index',
        port_expose=9090,
    )

    expected_traversed_executors = {
        'segmenter',
        'imageencoder',
        'textencoder',
    }

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert set(doc.tags['traversed-executors']) == expected_traversed_executors


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
        endpoint='/search',
        port_expose=9090,
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['file'] == ['1\n', '2\n', '3']


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
        endpoint='/index',
        port_expose=9090,
    )

    expected_traversed_executors = {
        'test_executor',
    }

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert set(doc.tags['traversed-executors']) == expected_traversed_executors


@pytest.mark.timeout(3600)
def test_flow_with_configmap(
    k8s_cluster,
    k8s_flow_configmap,
    load_images_in_kind,
    set_test_pip_version,
    logger,
):
    resp = run_test(
        k8s_flow_configmap,
        endpoint='/env',
        port_expose=9090,
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags.get('jina_log_level') == 'DEBUG'
        assert doc.tags.get('k1') == 'v1'
        assert doc.tags.get('k2') == 'v2'
        assert doc.tags.get('env') == {'k1': 'v1', 'k2': 'v2'}


@pytest.fixture()
def k8s_flow_with_reload_executor(
    reload_executor_image: str,
) -> Flow:
    flow = Flow(
        name='test-flow-with-reload',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
    ).add(
        name='test_executor',
        replicas=2,
        uses_with={'argument': 'value1'},
        uses=reload_executor_image,
        timeout_ready=120000,
    )
    return flow


def test_rolling_update_simple(
    k8s_cluster,
    k8s_flow_with_reload_executor,
    load_images_in_kind,
    set_test_pip_version,
    logger,
    reraise,
):
    from threading import Thread, Event
    import time

    def send_requests(flow_name, port_expose, client, event):
        from jina.peapods.pods.k8slib import kubernetes_tools

        with reraise:
            with kubernetes_tools.get_port_forward_contextmanager(
                flow_name, port_expose
            ):
                while not event.is_set():
                    r = client.post(
                        '/exec',
                        [Document() for _ in range(10)],
                        return_results=True,
                        port_expose=9090,
                    )
                    assert len(r) > 0
                    assert len(r[0].docs) > 0
                    for doc in r[0].docs:
                        assert doc.tags['argument'] in ['value1', 'value2']
                    time.sleep(0.1)

    with k8s_flow_with_reload_executor as flow:
        resp_v1 = flow.post(
            '/exec',
            [Document() for _ in range(10)],
            return_results=True,
            port_expose=9090,
        )
        assert len(resp_v1[0].docs) > 0
        for doc in resp_v1[0].docs:
            assert doc.tags['argument'] == 'value1'

        event = Event()
        thread = Thread(
            target=send_requests,
            kwargs={
                'flow_name': flow.args.name,
                'port_expose': 9090,
                'client': flow.client,
                'event': event,
            },
        )
        thread.start()
        time.sleep(0.5)
        flow.rolling_update('test_executor', uses_with={'argument': 'value2'})
        event.set()
        resp_v2 = flow.post(
            '/exec',
            [Document() for _ in range(10)],
            return_results=True,
            port_expose=9090,
        )

    assert len(resp_v1[0].docs) > 0
    for doc in resp_v1[0].docs:
        assert doc.tags['argument'] == 'value1'

    assert len(resp_v2[0].docs) > 0
    for doc in resp_v2[0].docs:
        assert doc.tags['argument'] == 'value2'
