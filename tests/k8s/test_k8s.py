# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
# You need to install linkerd cli on your local machine if you want to run the k8s tests https://linkerd.io/2.11/getting-started/#step-1-install-the-cli
import asyncio
import os

import pytest
import requests as req
import yaml
from docarray import DocumentArray

from jina import Client, Document, Executor, Flow, requests
from jina.helper import random_port
from jina.orchestrate.deployments import Deployment
from jina.orchestrate.deployments.config.k8s import K8sDeploymentConfig
from jina.parsers import set_deployment_parser
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from tests.helper import _validate_dummy_custom_gateway_response
from tests.k8s.conftest import shell_portforward
from tests.k8s.kind_wrapper import KindClusterWrapper


async def run_test(
    flow,
    k8s_cluster: KindClusterWrapper,
    namespace,
    endpoint,
    n_docs=10,
    request_size=100,
):
    from jina.clients import Client

    # TODO: This is probably bad practice but it's how the function used to work.
    # Port forwards should be to services not pods
    gateway_pod_name = k8s_cluster.get_pod_name(
        namespace=namespace, label_selector='app=gateway'
    )

    # start port forwarding
    with k8s_cluster.port_forward(
        gateway_pod_name, namespace=namespace, svc_port=flow.port, host_port=flow.port
    ):
        client_kwargs = dict(
            host='localhost',
            port=flow.port,
            asyncio=True,
        )
        client_kwargs.update(flow._common_kwargs)

        client = Client(**client_kwargs)
        client.show_progress = True
        try:
            responses = []
            async for resp in client.post(
                endpoint,
                inputs=[Document() for _ in range(n_docs)],
                request_size=request_size,
                return_responses=True,
            ):
                responses.append(resp)
        except Exception as e:
            # TODO: Remove this debug line or make it optional
            # breakpoint()
            raise e

    return responses


@pytest.fixture()
def k8s_flow_with_sharding(polling):
    flow = Flow(name='test-flow-with-sharding', port=9090, protocol='http').add(
        name='test_executor',
        shards=2,
        replicas=2,
        uses=f'docker://test-executor:test-pip',
        uses_after=f'docker://executor-merger:test-pip',
        polling=polling,
    )
    return flow


@pytest.fixture
def k8s_flow_configmap():
    flow = Flow(name='k8s-flow-configmap', port=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://test-executor:test-pip',
        env={'k1': 'v1', 'k2': 'v2'},
    )
    return flow


@pytest.fixture()
def jina_k3_env():
    import os

    os.environ['JINA_K3'] = '1'
    yield
    del os.environ['JINA_K3']


@pytest.fixture
def k8s_flow_gpu():
    flow = Flow(name='k8s-flow-gpu', port=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://test-executor:test-pip',
        gpus=1,
    )
    return flow


@pytest.fixture
def k8s_flow_with_needs():
    flow = (
        Flow(
            name='test-flow-with-needs',
            port=9090,
            protocol='http',
        )
        .add(
            name='segmenter',
            uses='docker://test-executor:test-pip',
        )
        .add(
            name='textencoder',
            uses='docker://test-executor:test-pip',
            needs='segmenter',
        )
        .add(
            name='imageencoder',
            uses='docker://test-executor:test-pip',
            needs='segmenter',
        )
        .add(
            name='merger',
            uses=f'docker://executor-merger:test-pip',
            needs=['imageencoder', 'textencoder'],
            disable_reduce=True,
        )
    )
    return flow


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_with_needs(
    k8s_flow_with_needs, tmpdir, k8s_cluster: KindClusterWrapper
):
    NAMESPACE = 'test-flow-with-needs'
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-needs')
    k8s_flow_with_needs.to_kubernetes_yaml(dump_path, k8s_namespace=NAMESPACE)

    k8s_cluster.deploy_from_dir(dump_path, namespace=NAMESPACE)
    resp = await run_test(
        flow=k8s_flow_with_needs,
        namespace=NAMESPACE,
        k8s_cluster=k8s_cluster,
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
    k8s_cluster.delete_namespace(NAMESPACE)


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
async def test_flow_with_sharding(
    k8s_flow_with_sharding, polling, tmpdir, k8s_cluster: KindClusterWrapper
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-sharding')
    namespace = f'test-flow-with-sharding-{polling}'.lower()
    k8s_flow_with_sharding.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)
    resp = await run_test(
        flow=k8s_flow_with_sharding,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/debug',
    )

    k8s_cluster.delete_namespace(namespace)
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
async def test_flow_with_configmap(
    k8s_flow_configmap, tmpdir, k8s_cluster: KindClusterWrapper
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-configmap')
    namespace = f'test-flow-with-configmap'.lower()
    k8s_flow_configmap.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)
    resp = await run_test(
        flow=k8s_flow_configmap,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/env',
    )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['JINA_LOG_LEVEL'] == 'INFO'
        assert doc.tags['k1'] == 'v1'
        assert doc.tags['k2'] == 'v2'
        assert doc.tags['env'] == {'k1': 'v1', 'k2': 'v2'}
    k8s_cluster.delete_namespace(namespace)


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.skip('Need to config gpu host.')
async def test_flow_with_gpu(k8s_flow_gpu, tmpdir, k8s_cluster: KindClusterWrapper):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-gpu')
    namespace = f'test-flow-with-gpu'
    k8s_flow_gpu.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    resp = await run_test(
        flow=k8s_flow_gpu,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/cuda',
    )
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['resources']['limits'] == {'nvidia.com/gpu:': 1}
    k8s_cluster.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_with_workspace(tmpdir, k8s_cluster: KindClusterWrapper):
    flow = Flow(name='k8s_flow-with_workspace', port=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://test-executor:test-pip',
        workspace='/shared',
    )

    dump_path = os.path.join(str(tmpdir), 'test-flow-with-workspace')
    namespace = f'test-flow-with-workspace'.lower()
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    resp = await run_test(
        flow=flow,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/workspace',
    )
    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['workspace'] == '/shared/TestExecutor/0'
    k8s_cluster.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_with_external_native_deployment(
    tmpdir, k8s_cluster: KindClusterWrapper
):
    class DocReplaceExecutor(Executor):
        @requests
        def add(self, **kwargs):
            return DocumentArray(
                [Document(text='executor was here') for _ in range(100)]
            )

    args = set_deployment_parser().parse_args(['--uses', 'DocReplaceExecutor'])
    with Deployment(args) as external_deployment:
        ports = [args.port for args in external_deployment.pod_args['pods'][0]]
        flow = Flow(name='k8s_flow-with_external_deployment', port=9090).add(
            name='external_executor',
            external=True,
            host=f'172.17.0.1',
            port=ports[0],
        )

        namespace = 'test-flow-with-external-deployment'
        dump_path = os.path.join(str(tmpdir), namespace)
        flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

        k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

        resp = await run_test(
            flow=flow,
            namespace=namespace,
            k8s_cluster=k8s_cluster,
            endpoint='/',
        )
    docs = resp[0].docs
    assert len(docs) == 100
    for doc in docs:
        assert doc.text == 'executor was here'
    k8s_cluster.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_with_external_k8s_deployment(
    tmpdir, k8s_cluster: KindClusterWrapper
):
    namespace = 'test-flow-with-external-k8s-deployment'
    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)

    await _create_external_deployment(
        api_client, app_client, 'test-executor:test-pip', tmpdir
    )

    flow = Flow(name='k8s_flow-with_external_deployment', port=9090).add(
        name='external_executor',
        external=True,
        host='external-deployment.external-deployment-ns.svc',
        port=GrpcConnectionPool.K8S_PORT,
    )

    dump_path = os.path.join(str(tmpdir), namespace)
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    resp = await run_test(
        flow=flow,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/workspace',
    )
    docs = resp[0].docs
    for doc in docs:
        assert 'workspace' in doc.tags


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize('grpc_metadata', [{}, {"key1": "value1"}])
async def test_flow_with_metadata_k8s_deployment(
    k8s_cluster: KindClusterWrapper, grpc_metadata, tmpdir
):
    namespace = 'test-flow-with-metadata-k8s-deployment'
    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)

    # TODO: This should not be necessary and tangles the above test with this one
    await _create_external_deployment(
        api_client, app_client, 'test-executor:test-pip', tmpdir
    )

    flow = Flow(name='k8s_flow-with_metadata_deployment', port=9090).add(
        name='external_executor',
        external=True,
        host='external-deployment.external-deployment-ns.svc',
        port=GrpcConnectionPool.K8S_PORT,
        grpc_metadata=grpc_metadata,
    )

    dump_path = os.path.join(str(tmpdir), namespace)
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    resp = await run_test(
        flow=flow,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/workspace',
    )
    docs = resp[0].docs
    for doc in docs:
        assert 'workspace' in doc.tags


async def _create_external_deployment(api_client, app_client, image_name, tmpdir):
    namespace = 'external-deployment-ns'
    args = set_deployment_parser().parse_args(
        ['--uses', f'docker://{image_name}', '--name', 'external-deployment']
    )
    external_deployment_config = K8sDeploymentConfig(args=args, k8s_namespace=namespace)
    configs = external_deployment_config.to_kubernetes_yaml()
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


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_with_failing_executor(tmpdir, k8s_cluster: KindClusterWrapper):
    flow = Flow(name='failing_flow-with_workspace', port=9090, protocol='http').add(
        name='failing_executor',
        uses=f'docker://failing-executor:test-pip',
        workspace='/shared',
        exit_on_exceptions=["Exception", "RuntimeError"],
    )

    dump_path = os.path.join(str(tmpdir), 'failing-flow-with-workspace')
    namespace = f'failing-flow-with-workspace'.lower()
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    from kubernetes import client

    api_client = client.ApiClient()
    core_client = client.CoreV1Api(api_client=api_client)
    app_client = client.AppsV1Api(api_client=api_client)
    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    try:
        await run_test(
            flow=flow,
            namespace=namespace,
            k8s_cluster=k8s_cluster,
            endpoint='/',
        )
    except:
        pass

    await asyncio.sleep(0.5)

    pods = core_client.list_namespaced_pod(namespace=namespace).items
    pod_restarts = [item.status.container_statuses[0].restart_count for item in pods]
    assert any([count for count in pod_restarts if count > 0])

    await asyncio.sleep(2)
    pods = core_client.list_namespaced_pod(namespace=namespace).items
    pod_phases = [item.status.phase for item in pods]
    assert all([phase == 'Running' for phase in pod_phases])

    k8s_cluster.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_with_custom_gateway(tmpdir, k8s_cluster: KindClusterWrapper):
    flow = (
        Flow(
            name='flow_with_custom_gateway',
        )
        .config_gateway(
            port=9090,
            protocol='http',
            uses='docker://custom-gateway:test-pip',
            uses_with={'arg1': 'overridden-hello'},
        )
        .add(
            name='test_executor',
            uses='docker://test-executor:test-pip',
        )
    )

    dump_path = os.path.join(str(tmpdir), 'k8s-flow-custom-gateway.yml')
    namespace = 'flow-custom-gateway'.lower()
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    gateway_pod_name = k8s_cluster.get_pod_name(
        namespace=namespace, label_selector='app=gateway'
    )

    with k8s_cluster.port_forward(
        gateway_pod_name, namespace=namespace, svc_port=flow.port, host_port=flow.port
    ):

        _validate_dummy_custom_gateway_response(
            flow.port,
            {'arg1': 'overridden-hello', 'arg2': 'world', 'arg3': 'default-arg3'},
        )
        import requests

        resp = requests.get(f'http://127.0.0.1:{flow.port}/stream?text=hello').json()
        assert resp['text'] == 'hello'
        tags = resp['tags']
        assert tags['traversed-executors'] == ['test_executor']
        assert tags['shards'] == 1
        assert tags['shard_id'] == 0

    k8s_cluster.delete_namespace(namespace)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_flow_multiple_protocols_gateway(tmpdir, k8s_cluster: KindClusterWrapper):
    http_port = random_port()
    grpc_port = random_port()
    flow = Flow().config_gateway(
        uses='docker://multiprotocol-gateway:test-pip',
        port=[http_port, grpc_port],
        protocol=['http', 'grpc'],
    )

    dump_path = os.path.join(str(tmpdir), 'k8s-flow-multiprotocol-gateway')
    namespace = 'flow-multiprotocol-gateway'
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace)

    gateway_pod_name = k8s_cluster.get_pod_name(
        namespace=namespace, label_selector='app=gateway'
    )

    # test portforwarding the gateway pod and service using http
    forward_args = [
        [gateway_pod_name, http_port, http_port, namespace],
        ['service/gateway', http_port, http_port, namespace],
    ]
    for forward in forward_args:
        with shell_portforward(k8s_cluster._cluster.kubectl_path, *forward):
            import requests

            resp = requests.get(f'http://localhost:{http_port}').json()
            assert resp['protocol'] == 'http'

    # test portforwarding the gateway pod and service using grpc
    forward_args = [
        [gateway_pod_name, grpc_port, grpc_port, namespace],
        ['service/gateway-1-grpc', grpc_port, grpc_port, namespace],
    ]
    for forward in forward_args:
        with shell_portforward(k8s_cluster._cluster.kubectl_path, *forward):
            grpc_client = Client(protocol='grpc', port=grpc_port, asyncio=True)
            async for _ in grpc_client.post('/', inputs=DocumentArray.empty(5)):
                pass
            assert AsyncNewLoopRuntime.is_ready(f'localhost:{grpc_port}')


@pytest.mark.skip(
    reason='This test does not work. If you take the old test and slow down the namespace deletion, it will fail the assert. Ask Joan about this'
)
@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize('workspace_path', ['workspace_path'])
async def test_flow_with_stateful_executor(
    tmpdir, k8s_cluster: KindClusterWrapper, workspace_path
):
    dump_path = os.path.join(str(tmpdir), 'test-flow-with-volumes')
    namespace = f'test-flow-with-volumes'.lower()
    flow = Flow(name='test-flow-with-volumes', port=9090, protocol='http').add(
        name='statefulexecutor',
        uses=f'docker://test-stateful-executor:test-pip',
        workspace=f'{str(tmpdir)}/workspace_path',
        volumes=str(tmpdir),
    )
    flow.to_kubernetes_yaml(dump_path, k8s_namespace=namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace, validate=False)

    await run_test(
        flow=flow,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/index',
    )

    k8s_cluster.delete_namespace(namespace)

    k8s_cluster.deploy_from_dir(dump_path, namespace=namespace, validate=False)

    resp = await run_test(
        flow=flow,
        namespace=namespace,
        k8s_cluster=k8s_cluster,
        endpoint='/len',
    )

    assert len(resp) == 1
    assert resp[0].parameters == {'__results__': {'statefulexecutor': {'length': 10.0}}}
