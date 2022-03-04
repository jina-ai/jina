# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
import pytest
import os
import asyncio

import yaml
from pytest_kind import cluster

from docarray import DocumentArray
from jina import Executor, Flow, Document, requests
from jina.orchestrate.deployments import Deployment
from jina.orchestrate.deployments.config.k8s import K8sDeploymentConfig
from jina.parsers import set_deployment_parser
from jina.serve.networking import GrpcConnectionPool

cluster.KIND_VERSION = 'v0.11.1'


async def create_all_flow_deployments_and_wait_ready(
    flow_dump_path,
    namespace,
    api_client,
    app_client,
    core_client,
    deployment_replicas_expected,
    logger,
):
    from kubernetes import utils

    namespace = namespace.lower()
    namespace_object = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {'name': f'{namespace}'},
    }
    try:
        logger.info(f'create Namespace {namespace}')
        utils.create_from_dict(api_client, namespace_object)
    except:
        pass

    while True:
        ns_items = core_client.list_namespace().items
        if any(item.metadata.name == namespace for item in ns_items):
            logger.info(f'created Namespace {namespace}')
            break
        logger.info(f'waiting for Namespace {namespace}')
        await asyncio.sleep(1.0)

    deployment_set = set(os.listdir(flow_dump_path))
    for deployment_name in deployment_set:
        file_set = set(os.listdir(os.path.join(flow_dump_path, deployment_name)))
        for file in file_set:
            try:
                utils.create_from_yaml(
                    api_client,
                    yaml_file=os.path.join(flow_dump_path, deployment_name, file),
                    namespace=namespace,
                )
            except Exception as e:
                # some objects are not successfully created since they exist from previous files
                logger.info(
                    f'Did not create ressource from {file} for pod {deployment_name} due to {e} '
                )
                pass

    # wait for all the pods to be up
    expected_deployments = sum(deployment_replicas_expected.values())
    while True:
        namespaced_pods = core_client.list_namespaced_pod(namespace)
        if (
            namespaced_pods.items is not None
            and len(namespaced_pods.items) == expected_deployments
        ):
            break
        logger.info(
            f'Waiting for all {expected_deployments} Deployments to be created, only got {len(namespaced_pods.items) if namespaced_pods.items is not None else None}'
        )
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
        logger.info(f'Waiting for {deployment_names} to be ready')
        await asyncio.sleep(1.0)


async def run_test(flow, core_client, namespace, endpoint, n_docs=10, request_size=100):
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
        namespace, gateway_pod_name, flow.port, flow.port, config_path
    ):
        client_kwargs = dict(
            host='localhost',
            port=flow.port,
            return_responses=True,
            asyncio=True,
        )
        client_kwargs.update(flow._common_kwargs)

        client = Client(**client_kwargs)
        client.show_progress = True
        responses = []
        async for resp in client.post(
            endpoint,
            inputs=[Document() for _ in range(n_docs)],
            request_size=request_size,
        ):
            responses.append(resp)

    return responses


@pytest.fixture()
def k8s_flow_with_sharding(docker_images, polling):
    flow = Flow(name='test-flow-with-sharding', port=9090, protocol='http').add(
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
    flow = Flow(name='k8s-flow-configmap', port=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        env={'k1': 'v1', 'k2': 'v2'},
    )
    return flow


@pytest.fixture
def k8s_flow_gpu(docker_images):
    flow = Flow(name='k8s-flow-gpu', port=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        gpus=1,
    )
    return flow


@pytest.fixture
def k8s_flow_with_reload_executor(docker_images):
    flow = Flow(name='test-flow-with-reload', port=9090, protocol='http').add(
        name='test_executor',
        replicas=2,
        uses_with={'argument': 'value1'},
        uses=f'docker://{docker_images[0]}',
    )
    return flow


@pytest.fixture
def k8s_flow_scale(docker_images, shards):
    DEFAULT_REPLICAS = 2

    flow = Flow(name='test-flow-scale', port=9090, protocol='http').add(
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
            port=9090,
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
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_needs(logger, k8s_flow_with_needs, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-needs')
    namespace = f'test-flow-with-needs'.lower()
    k8s_flow_with_needs.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'segmenter-head': 1,
            'segmenter': 1,
            'textencoder-head': 1,
            'textencoder': 1,
            'imageencoder-head': 1,
            'imageencoder': 1,
            'merger-head': 1,
            'merger': 1,
        },
        logger=logger,
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
    core_client.delete_namespace(namespace)


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
async def test_flow_with_sharding(k8s_flow_with_sharding, polling, tmpdir, logger):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-sharding')
    namespace = f'test-flow-with-sharding-{polling}'.lower()
    k8s_flow_with_sharding.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head': 1,
            'test-executor-0': 2,
            'test-executor-1': 2,
        },
        logger=logger,
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
            assert set(doc.tags['shard_id']) == {0, 1}
            assert doc.tags['parallel'] == [2, 2]
            assert doc.tags['shards'] == [2, 2]
        else:
            assert len(set(doc.tags['traversed-executors'])) == 1
            assert set(doc.tags['traversed-executors']) == {'test_executor-0'} or set(
                doc.tags['traversed-executors']
            ) == {'test_executor-1'}
            assert len(set(doc.tags['shard_id'])) == 1
            assert 0 in set(doc.tags['shard_id']) or 1 in set(doc.tags['shard_id'])
            assert doc.tags['parallel'] == [2]
            assert doc.tags['shards'] == [2]


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['test-executor', 'jinaai/jina']], indirect=True
)
async def test_flow_with_configmap(k8s_flow_configmap, docker_images, tmpdir, logger):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-configmap')
    namespace = f'test-flow-with-configmap'.lower()
    k8s_flow_configmap.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head': 1,
            'test-executor': 1,
        },
        logger=logger,
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
    core_client.delete_namespace(namespace)


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.skip('Need to config gpu host.')
@pytest.mark.parametrize(
    'docker_images', [['test-executor', 'jinaai/jina']], indirect=True
)
async def test_flow_with_gpu(k8s_flow_gpu, docker_images, tmpdir, logger):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-gpu')
    namespace = f'test-flow-with-gpu'
    k8s_flow_gpu.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head': 1,
            'test-executor': 1,
        },
        logger=logger,
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
    core_client.delete_namespace(namespace)


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['reload-executor', 'jinaai/jina']], indirect=True
)
async def test_rolling_update_simple(
    k8s_flow_with_reload_executor, docker_images, tmpdir, logger
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-reload')
    namespace = f'test-flow-with-reload-executor'
    k8s_flow_with_reload_executor.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head': 1,
            'test-executor': 2,
        },
        logger=logger,
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
    core_client.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_workspace(logger, docker_images, tmpdir):
    flow = Flow(name='k8s_flow-with_workspace', port=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        workspace='/shared',
    )

    dump_path = os.path.join(str(tmpdir), 'test-flow-with-workspace')
    namespace = f'test-flow-with-workspace'.lower()
    flow.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
            'test-executor-head': 1,
            'test-executor': 1,
        },
        logger=logger,
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
        assert doc.tags['workspace'] == '/shared/TestExecutor/0'
    core_client.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['jinaai/jina']],
    indirect=True,
)
async def test_flow_with_external_native_deployment(logger, docker_images, tmpdir):
    class DocReplaceExecutor(Executor):
        @requests
        def add(self, **kwargs):
            return DocumentArray(
                [Document(text='executor was here') for _ in range(100)]
            )

    args = set_deployment_parser().parse_args(['--uses', 'DocReplaceExecutor'])
    with Deployment(args) as external_deployment:
        flow = Flow(name='k8s_flow-with_external_deployment', port=9090).add(
            name='external_executor',
            external=True,
            host=f'172.17.0.1',
            port=external_deployment.head_port,
        )

        namespace = 'test-flow-with-external-deployment'
        dump_path = os.path.join(str(tmpdir), namespace)
        flow.to_k8s_yaml(dump_path, k8s_namespace=namespace)

        from kubernetes import client

        api_client = client.ApiClient()
        core_client = client.CoreV1Api(api_client=api_client)
        app_client = client.AppsV1Api(api_client=api_client)
        await create_all_flow_deployments_and_wait_ready(
            dump_path,
            namespace=namespace,
            api_client=api_client,
            app_client=app_client,
            core_client=core_client,
            deployment_replicas_expected={
                'gateway': 1,
            },
            logger=logger,
        )
        resp = await run_test(
            flow=flow,
            namespace=namespace,
            core_client=core_client,
            endpoint='/',
        )
    docs = resp[0].docs
    assert len(docs) == 100
    for doc in docs:
        assert doc.text == 'executor was here'
    core_client.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_external_k8s_deployment(logger, docker_images, tmpdir):
    namespace = 'test-flow-with-external-k8s-deployment'
    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)

    await _create_external_deployment(api_client, app_client, docker_images, tmpdir)

    flow = Flow(name='k8s_flow-with_external_deployment', port=9090).add(
        name='external_executor',
        external=True,
        host='external-deployment-head.external-deployment-ns.svc',
        port=GrpcConnectionPool.K8S_PORT,
    )

    dump_path = os.path.join(str(tmpdir), namespace)
    flow.to_k8s_yaml(dump_path, k8s_namespace=namespace)

    await create_all_flow_deployments_and_wait_ready(
        dump_path,
        namespace=namespace,
        api_client=api_client,
        app_client=app_client,
        core_client=core_client,
        deployment_replicas_expected={
            'gateway': 1,
        },
        logger=logger,
    )

    resp = await run_test(
        flow=flow,
        namespace=namespace,
        core_client=core_client,
        endpoint='/workspace',
    )
    docs = resp[0].docs
    for doc in docs:
        assert 'workspace' in doc.tags


async def _create_external_deployment(api_client, app_client, docker_images, tmpdir):
    namespace = 'external-deployment-ns'
    args = set_deployment_parser().parse_args(
        ['--uses', f'docker://{docker_images[0]}', '--name', 'external-deployment']
    )
    external_deployment_config = K8sDeploymentConfig(args=args, k8s_namespace=namespace)
    configs = external_deployment_config.to_k8s_yaml()
    deployment_base = os.path.join(tmpdir, 'external-deployment')
    filenames = []
    for name, k8s_objects in configs:
        filename = os.path.join(deployment_base, f'{name}.yml')
        os.makedirs(deployment_base, exist_ok=True)
        with open(filename, 'w+') as fp:
            filenames.append(filename)
            for i, k8s_object in enumerate(k8s_objects):
                yaml.dump(k8s_object, fp)
                if i < len(k8s_objects) - 1:
                    fp.write('---\n')
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

    for filename in filenames:
        try:
            utils.create_from_yaml(
                api_client,
                yaml_file=filename,
                namespace=namespace,
            )
        except:
            pass

    await asyncio.sleep(1.0)
