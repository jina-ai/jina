# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
from pytest_kind import cluster
import pytest
from jina import Flow, Document
from jina.peapods.pods.k8slib.kubernetes_client import K8sClients

cluster.KIND_VERSION = 'v0.11.1'


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
def k8s_flow_with_init_container(k8s_cluster, image_name_tag_map):
    image_names = ['test-executor', 'dummy-dumper']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    flow = Flow(
        name='test-flow-with-init-container',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
        k8s_namespace='test-flow-with-init-container-ns',
    ).add(
        name='test_executor',
        uses=images[0],
        k8s_init_container_command=["python", "dump.py", "/shared/test_file.txt"],
        k8s_uses_init=images[1],
        k8s_mount_path='/shared',
        timeout_ready=120000,
    )
    return flow


@pytest.fixture()
def k8s_flow_with_sharding(k8s_cluster, image_name_tag_map):
    image_names = ['test-executor', 'executor-merger']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    flow = Flow(
        name='test-flow-with-sharding',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
        k8s_namespace='test-flow-with-sharding-ns',
    ).add(
        name='test_executor',
        shards=2,
        replicas=2,
        uses=images[0],
        uses_after=images[1],
        timeout_ready=360000,
    )
    return flow


@pytest.fixture
def k8s_flow_configmap(k8s_cluster, image_name_tag_map):
    image_names = ['test-executor']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    flow = Flow(
        name='k8s-flow-configmap',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
        k8s_namespace='k8s-flow-configmap-ns',
    ).add(
        name='test_executor',
        uses=images[0],
        timeout_ready=12000,
        env={'k1': 'v1', 'k2': 'v2'},
    )
    return flow


@pytest.fixture
def k8s_flow_gpu(k8s_cluster, image_name_tag_map):
    image_names = ['test-executor']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    flow = Flow(
        name='k8s-flow-gpu',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
        k8s_namespace='k8s-flow-gpu-ns',
    ).add(
        name='test_executor',
        uses=images[0],
        timeout_ready=12000,
        gpus=1,
    )
    return flow


@pytest.fixture
def k8s_flow_with_reload_executor(k8s_cluster, image_name_tag_map):
    image_names = ['reload-executor']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
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
        uses=images[0],
        timeout_ready=120000,
    )
    return flow


@pytest.fixture
def k8s_flow_with_namespace():
    flow = Flow(
        name='test-flow-with-namespace',
        port_expose=9090,
        infrastructure='K8S',
        protocol='http',
        timeout_ready=120000,
        k8s_namespace='my-custom-namespace',
    ).add(
        name='test_executor',
    )
    return flow


@pytest.mark.timeout(3600)
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
def test_flow_with_needs(
    k8s_cluster,
    logger,
    k8s_connection_pool,
    image_name_tag_map,
):
    image_names = ['test-executor', 'executor-merger']
    images = [
        image_name + ':' + image_name_tag_map[image_name] for image_name in image_names
    ]
    k8s_cluster.load_docker_images(image_names, image_name_tag_map)
    flow_name = 'test-flow-with-needs'
    if k8s_connection_pool:
        flow_name += '-pool'
    flow = (
        Flow(
            name=flow_name,
            port_expose=9090,
            infrastructure='K8S',
            protocol='http',
            timeout_ready=120000,
            k8s_disable_connection_pool=not k8s_connection_pool,
            k8s_namespace=flow_name + '-ns',
        )
        .add(
            name='segmenter',
            uses=images[0],
            timeout_ready=120000,
        )
        .add(
            name='textencoder',
            uses=images[0],
            needs='segmenter',
            timeout_ready=120000,
        )
        .add(
            name='imageencoder',
            uses=images[0],
            needs='segmenter',
            timeout_ready=120000,
        )
        .add(
            name='merger',
            uses=images[1],
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

    for pod in flow._pod_nodes.values():
        assert pod.args.k8s_connection_pool == k8s_connection_pool
        for peapod in pod.k8s_deployments:
            assert peapod.deployment_args.k8s_connection_pool == k8s_connection_pool


@pytest.mark.timeout(3600)
def test_flow_with_init(
    k8s_flow_with_init_container,
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
    k8s_flow_with_sharding,
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
        assert set(doc.tags['pea_id']) == {0, 1}
        assert set(doc.tags['shard_id']) == {0, 1}
        assert doc.tags['parallel'] == [2, 2]
        assert doc.tags['shards'] == [2, 2]


@pytest.mark.timeout(3600)
def test_flow_with_configmap(
    k8s_flow_configmap,
):
    resp = run_test(
        k8s_flow_configmap,
        endpoint='/env',
        port_expose=9090,
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags.get('JINA_LOG_LEVEL') == 'DEBUG'
        assert doc.tags.get('k1') == 'v1'
        assert doc.tags.get('k2') == 'v2'
        assert doc.tags.get('env') == {'k1': 'v1', 'k2': 'v2'}


@pytest.mark.timeout(3600)
@pytest.mark.skip('Need to config gpu host.')
def test_flow_with_gpu(
    k8s_flow_gpu,
):
    resp = run_test(
        k8s_flow_gpu,
        endpoint='/cuda',
        port_expose=9090,
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['resources']['limits'] == {'nvidia.com/gpu:': 1}


@pytest.mark.timeout(3600)
def test_flow_with_k8s_namespace(
    k8s_flow_with_namespace,
):
    with k8s_flow_with_namespace as f:
        client = K8sClients().core_v1
        namespaces = client.list_namespace().items
        namespaces = [item.metadata.name for item in namespaces]
        assert 'my-custom-namespace' in namespaces


def test_rolling_update_simple(
    k8s_flow_with_reload_executor,
    logger,
    reraise,
):
    from jina.peapods.pods.k8slib import kubernetes_tools
    from multiprocessing import Process, Event
    import time

    def send_requests(
        client_kwargs,
        rolling_event,
        client_ready_to_send_event,
        exception_to_raise_event,
    ):
        from jina.logging.logger import JinaLogger
        from jina.clients import Client

        _logger = JinaLogger('test_send_requests')
        _logger.debug(f' send request start')
        try:
            client = Client(**client_kwargs)
            client.show_progress = True
            _logger.debug(f' Client instantiated with {client_kwargs}')
            _logger.debug(f' Set client_ready_to_send_event event')
            client_ready_to_send_event.set()
            while not rolling_event.is_set():
                _logger.debug(f' event is not set')
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
                _logger.debug(f' event is unset')
        except:
            _logger.error(f' Some error happened while sending requests')
            exception_to_raise_event.set()
        _logger.debug(f' send requests finished')

    with k8s_flow_with_reload_executor as flow:
        with kubernetes_tools.get_port_forward_contextmanager(
            'test-flow-with-reload', 9090
        ):
            resp_v1 = flow.post(
                '/exec',
                [Document() for _ in range(10)],
                return_results=True,
                port_expose=9090,
                disable_portforward=True,
            )
            assert len(resp_v1[0].docs) > 0
            for doc in resp_v1[0].docs:
                assert doc.tags['argument'] == 'value1'

            rolling_update_finished_event = Event()
            client_ready_to_send = Event()
            exception_to_raise = Event()
            client_kwargs = dict(
                host='localhost',
                port=9090,
                protocol='http',
            )
            client_kwargs.update(flow._common_kwargs)
            process = Process(
                target=send_requests,
                kwargs={
                    'client_kwargs': client_kwargs,
                    'rolling_event': rolling_update_finished_event,
                    'client_ready_to_send_event': client_ready_to_send,
                    'exception_to_raise_event': exception_to_raise,
                },
                daemon=True,
            )
            process.start()
            logger.debug(f' Waiting for client to be ready to send')
            client_ready_to_send.wait(10000.0)
            logger.debug(f' Waiting for client to be ready to send')
            flow.rolling_update('test_executor', uses_with={'argument': 'value2'})
            rolling_update_finished_event.set()
            time.sleep(0.5)
            resp_v2 = flow.post(
                '/exec',
                [Document() for _ in range(10)],
                return_results=True,
                port_expose=9090,
                disable_portforward=True,
            )
        logger.debug(f' Joining the process')
        process.join()
        logger.debug(f' Process succesfully joined')

    assert not exception_to_raise.set()

    assert len(resp_v1[0].docs) > 0
    for doc in resp_v1[0].docs:
        assert doc.tags['argument'] == 'value1'

    assert len(resp_v2[0].docs) > 0
    for doc in resp_v2[0].docs:
        assert doc.tags['argument'] == 'value2'
