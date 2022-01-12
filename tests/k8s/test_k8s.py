# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
import pytest
import os
import asyncio

from pytest_kind import cluster

from jina import Flow, Document

cluster.KIND_VERSION = 'v0.11.1'


async def create_all_flow_pods_and_wait_ready(
    flow_dump_path,
    namespace,
    api_client,
    app_client,
    core_client,
    deployment_replicas_expected,
):
    from kubernetes import utils

    namespace_object = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {'name': f'{namespace}'},
    }
    try:
        utils.create_from_dict(api_client, namespace_object)
    except:
        pass

    pod_set = set(os.listdir(flow_dump_path))
    for pod_name in pod_set:
        file_set = set(os.listdir(os.path.join(flow_dump_path, pod_name)))
        for file in file_set:
            try:
                utils.create_from_yaml(
                    api_client,
                    yaml_file=os.path.join(flow_dump_path, pod_name, file),
                    namespace=namespace,
                )
            except Exception:
                # some objects are not successfully created since they exist from previous files
                pass

    # wait for all the pods to be up
    while True:
        namespaced_pods = core_client.list_namespaced_pod(namespace)
        if namespaced_pods.items is not None and len(namespaced_pods.items) == sum(
            deployment_replicas_expected.values()
        ):
            break
        await asyncio.sleep(1.0)

    # wait for all the pods to be up
    resp = app_client.list_namespaced_deployment(namespace=namespace)
    deployment_names = set([item.metadata.name for item in resp.items])
    assert deployment_names == set(deployment_replicas_expected.keys())
    while len(deployment_names) > 0:
        deployments_ready = []
        for deployment_name in deployment_names:
            api_response = app_client.read_namespaced_deployment(
                name=deployment_name, namespace=namespace
            )
            expected_num_replicas = deployment_replicas_expected[deployment_name]
            if (
                api_response.status.ready_replicas is not None
                and api_response.status.ready_replicas == expected_num_replicas
            ):
                deployments_ready.append(deployment_name)

        for deployment_name in deployments_ready:
            deployment_names.remove(deployment_name)
        await asyncio.sleep(1.0)


async def run_test(flow, core_client, namespace, endpoint):
    # start port forwarding
    from jina.clients import Client

    gateway_pod_name = (
        core_client.list_namespaced_pod(
            namespace=namespace, label_selector='app=gateway'
        )
        .items[0]
        .metadata.name
    )
    config_path = os.environ['KUBECONFIG']
    import portforward

    with portforward.forward(
        namespace, gateway_pod_name, flow.port_expose, flow.port_expose, config_path
    ):
        client_kwargs = dict(
            host='localhost',
            port=flow.port_expose,
            asyncio=True,
        )
        client_kwargs.update(flow._common_kwargs)

        client = Client(**client_kwargs)
        client.show_progress = True
        responses = []
        async for resp in client.post(
            endpoint, inputs=[Document() for _ in range(10)], return_results=True
        ):
            responses.append(resp)

    return responses


@pytest.fixture()
def k8s_flow_with_sharding(docker_images, polling):
    flow = Flow(name='test-flow-with-sharding', port_expose=9090, protocol='http').add(
        name='test_executor',
        shards=2,
        replicas=2,
        uses=f'docker://{docker_images[0]}',
        uses_after=f'docker://{docker_images[1]}',
        polling=polling,
    )
    return flow


@pytest.fixture
def k8s_flow_configmap(docker_images):
    flow = Flow(name='k8s-flow-configmap', port_expose=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        env={'k1': 'v1', 'k2': 'v2'},
    )
    return flow


@pytest.fixture
def k8s_flow_gpu(docker_images):
    flow = Flow(name='k8s-flow-gpu', port_expose=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        gpus=1,
    )
    return flow


@pytest.fixture
def k8s_flow_with_reload_executor(docker_images):
    flow = Flow(name='test-flow-with-reload', port_expose=9090, protocol='http').add(
        name='test_executor',
        replicas=2,
        uses_with={'argument': 'value1'},
        uses=f'docker://{docker_images[0]}',
    )
    return flow


@pytest.fixture
def k8s_flow_scale(docker_images, shards):
    DEFAULT_REPLICAS = 2

    flow = Flow(name='test-flow-scale', port_expose=9090, protocol='http').add(
        name='test_executor',
        shards=shards,
        replicas=DEFAULT_REPLICAS,
    )
    return flow


@pytest.fixture
def k8s_flow_with_needs(docker_images):
    flow = (
        Flow(
            name='test-flow-with-needs',
            port_expose=9090,
            protocol='http',
        )
        .add(
            name='segmenter',
            uses=f'docker://{docker_images[0]}',
        )
        .add(
            name='textencoder',
            uses=f'docker://{docker_images[0]}',
            needs='segmenter',
        )
        .add(
            name='imageencoder',
            uses=f'docker://{docker_images[0]}',
            needs='segmenter',
        )
        .add(
            name='merger',
            uses_before=f'docker://{docker_images[1]}',
            needs=['imageencoder', 'textencoder'],
        )
    )
    return flow


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_needs(
    logger, k8s_connection_pool, k8s_flow_with_needs, tmpdir
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-needs')
    namespace = f'test-flow-with-needs-{k8s_connection_pool}'.lower()
    k8s_flow_with_needs.to_k8s_yaml(
        dump_path, k8s_namespace=namespace, k8s_connection_pool=k8s_connection_pool
    )

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_pods_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'segmenter-head-0': 1,
            'segmenter': 1,
            'textencoder-head-0': 1,
            'textencoder': 1,
            'imageencoder-head-0': 1,
            'imageencoder': 1,
            'merger-head-0': 1,
            'merger': 1,
        },
    )
    resp = await run_test(
        flow=k8s_flow_with_needs,
        namespace=namespace,
        core_client=core_client,
        endpoint='/debug',
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
@pytest.mark.asyncio
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
async def test_flow_with_sharding(
    k8s_flow_with_sharding, k8s_connection_pool, polling, tmpdir
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-sharding')
    namespace = f'test-flow-with-sharding-{polling}-{k8s_connection_pool}'.lower()
    k8s_flow_with_sharding.to_k8s_yaml(
        dump_path, k8s_namespace=namespace, k8s_connection_pool=k8s_connection_pool
    )

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_pods_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head-0': 1,
            'test-executor-0': 2,
            'test-executor-1': 2,
        },
    )
    resp = await run_test(
        flow=k8s_flow_with_sharding,
        namespace=namespace,
        core_client=core_client,
        endpoint='/debug',
    )

    core_client.delete_namespace(namespace)
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        if polling == 'ALL':
            assert set(doc.tags['traversed-executors']) == {
                'test_executor-0',
                'test_executor-1',
            }
            assert set(doc.tags['pea_id']) == {0, 1}
            assert set(doc.tags['shard_id']) == {0, 1}
            assert doc.tags['parallel'] == [2, 2]
            assert doc.tags['shards'] == [2, 2]
        else:
            assert len(set(doc.tags['traversed-executors'])) == 1
            assert set(doc.tags['traversed-executors']) == {'test_executor-0'} or set(
                doc.tags['traversed-executors']
            ) == {'test_executor-1'}
            assert len(set(doc.tags['pea_id'])) == 1
            assert len(set(doc.tags['shard_id'])) == 1
            assert 0 in set(doc.tags['pea_id']) or 1 in set(doc.tags['pea_id'])
            assert 0 in set(doc.tags['shard_id']) or 1 in set(doc.tags['shard_id'])
            assert doc.tags['parallel'] == [2]
            assert doc.tags['shards'] == [2]


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
@pytest.mark.parametrize(
    'docker_images', [['test-executor', 'jinaai/jina']], indirect=True
)
async def test_flow_with_configmap(
    k8s_flow_configmap, k8s_connection_pool, docker_images, tmpdir
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-configmap')
    namespace = f'test-flow-with-configmap-{k8s_connection_pool}'.lower()
    k8s_flow_configmap.to_k8s_yaml(
        dump_path, k8s_namespace=namespace, k8s_connection_pool=k8s_connection_pool
    )

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_pods_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head-0': 1,
            'test-executor': 1,
        },
    )
    resp = await run_test(
        flow=k8s_flow_configmap,
        namespace=namespace,
        core_client=core_client,
        endpoint='/env',
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['JINA_LOG_LEVEL'] == 'INFO'
        assert doc.tags['k1'] == 'v1'
        assert doc.tags['k2'] == 'v2'
        assert doc.tags['env'] == {'k1': 'v1', 'k2': 'v2'}


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.skip('Need to config gpu host.')
@pytest.mark.parametrize(
    'docker_images', [['test-executor', 'jinaai/jina']], indirect=True
)
async def test_flow_with_gpu(k8s_flow_gpu, docker_images, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-gpu')
    namespace = f'test-flow-with-gpu'
    k8s_flow_gpu.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_pods_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head-0': 1,
            'test-executor': 1,
        },
    )
    resp = await run_test(
        flow=k8s_flow_gpu,
        namespace=namespace,
        core_client=core_client,
        endpoint='/cuda',
    )
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['resources']['limits'] == {'nvidia.com/gpu:': 1}


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['reload-executor', 'jinaai/jina']], indirect=True
)
async def test_rolling_update_simple(
    k8s_flow_with_reload_executor, docker_images, tmpdir
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-reload')
    namespace = f'test-flow-with-reload-executor'
    k8s_flow_with_reload_executor.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_pods_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head-0': 1,
            'test-executor': 2,
        },
    )
    resp = await run_test(
        flow=k8s_flow_with_reload_executor,
        namespace=namespace,
        core_client=core_client,
        endpoint='/exec',
    )
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['argument'] == 'value1'

    import yaml

    with open(os.path.join(dump_path, 'test_executor', 'test-executor.yml')) as f:
        yml_document_all = list(yaml.safe_load_all(f))

    yml_deployment = yml_document_all[-1]
    container_args = yml_deployment['spec']['template']['spec']['containers'][0]['args']
    container_args[container_args.index('--uses-with') + 1] = '{"argument": "value2"}'
    yml_deployment['spec']['template']['spec']['containers'][0]['args'] = container_args
    app_client.patch_namespaced_deployment(
        name='test-executor', namespace=namespace, body=yml_deployment
    )
    await asyncio.sleep(10.0)
    resp = await run_test(
        flow=k8s_flow_with_reload_executor,
        namespace=namespace,
        core_client=core_client,
        endpoint='/index',
    )
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['argument'] == 'value2'


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize('k8s_connection_pool', [True, False])
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_workspace(logger, k8s_connection_pool, docker_images, tmpdir):
    flow = Flow(name='k8s_flow-with_workspace', port_expose=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        workspace='/shared',
    )

    dump_path = os.path.join(str(tmpdir), 'test-flow-with-workspace')
    namespace = f'test-flow-with-workspace'
    flow.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_pods_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head-0': 1,
            'test-executor': 1,
        },
    )
    resp = await run_test(
        flow=flow,
        namespace=namespace,
        core_client=core_client,
        endpoint='/workspace',
    )
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['workspace'] == '/shared/TestExecutor/0/0'
