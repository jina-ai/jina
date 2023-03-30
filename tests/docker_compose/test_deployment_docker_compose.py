# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
import os
import pytest
import requests as req
from jina.helper import random_port

from jina import Client, Document, Deployment
from tests.docker_compose.conftest import DockerComposeServices


async def run_test(port, endpoint, num_docs=10, request_size=10):
    # start port forwarding
    client_kwargs = dict(
        host='localhost',
        port=port,
        asyncio=True,
    )

    client = Client(**client_kwargs)
    client.show_progress = True
    responses = []
    async for resp in client.post(
            endpoint,
            inputs=[Document() for _ in range(num_docs)],
            request_size=request_size,
            return_responses=True,
    ):
        responses.append(resp)

    return responses


@pytest.fixture()
def deployment_with_replicas_with_sharding(docker_images, polling):
    deployment = Deployment(
        name='test_executor_replicas_sharding',
        port=9090,
        shards=2,
        replicas=2,
        uses=f'docker://{docker_images[0]}',
        uses_after=f'docker://{docker_images[1]}',
        polling=polling,
    )
    return deployment


@pytest.fixture()
def deployment_without_replicas_without_sharding(docker_images):
    deployment = Deployment(
        name='test_executor',
        port=9090,
        uses=f'docker://{docker_images[0]}',
    )
    return deployment


@pytest.fixture()
def deployment_with_replicas_without_sharding(docker_images):
    deployment = Deployment(
        name='test_executor_replicas',
        port=9090,
        replicas=2,
        uses=f'docker://{docker_images[0]}',
    )
    return deployment


@pytest.fixture()
def deployment_without_replicas_with_sharding(docker_images):
    deployment = Deployment(
        name='test_executor_sharding',
        port=9090,
        shards=2,
        uses=f'docker://{docker_images[0]}',
    )
    return deployment


@pytest.fixture
def deployment_configmap(docker_images):
    deployment = Deployment(
        port=9091,
        name='test_executor_configmap',
        uses=f'docker://{docker_images[0]}',
        env={'k1': 'v1', 'k2': 'v2'},
    )
    return deployment


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
async def test_deployment_monitoring(tmpdir, docker_images, port_generator):
    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-monitoring.yml')
    port1 = port_generator()

    deployment = Deployment(
        monitoring=True,
        port_monitoring=port1,
        name='segmenter',
        uses=f'docker://{docker_images[0]}',
    )
    deployment.to_docker_compose_yaml(dump_path, 'default')
    with DockerComposeServices(dump_path):
        resp = req.get(f'http://localhost:{port1}/')
        assert resp.status_code == 200


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
async def test_deployment_with_replicas_with_sharding(deployment_with_replicas_with_sharding, polling, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-with-replicas-with-sharding.yml')
    deployment_with_replicas_with_sharding.to_docker_compose_yaml(dump_path)

    with DockerComposeServices(dump_path):
        resp = await run_test(
            port=deployment_with_replicas_with_sharding.port, endpoint='/debug', num_docs=10, request_size=1
        )

    assert len(resp) == 10
    docs = resp[0].docs
    for r in resp[1:]:
        docs.extend(r.docs)
    assert len(docs) == 10

    runtimes_to_visit = {
        'test_executor_replicas_sharding-0/rep-0',
        'test_executor_replicas_sharding-1/rep-0',
        'test_executor_replicas_sharding-0/rep-1',
        'test_executor_replicas_sharding-1/rep-1',
    }

    for doc in docs:
        if polling == 'ALL':
            assert len(set(doc.tags['traversed-executors'])) == 2
            assert set(doc.tags['shard_id']) == {0, 1}
            assert doc.tags['parallel'] == [2, 2]
            assert doc.tags['shards'] == [2, 2]
            for executor in doc.tags['traversed-executors']:
                if executor in runtimes_to_visit:
                    runtimes_to_visit.remove(executor)
        else:
            assert len(set(doc.tags['traversed-executors'])) == 1
            assert len(set(doc.tags['shard_id'])) == 1
            assert 0 in set(doc.tags['shard_id']) or 1 in set(doc.tags['shard_id'])
            assert doc.tags['parallel'] == [2]
            assert doc.tags['shards'] == [2]
            for executor in doc.tags['traversed-executors']:
                if executor in runtimes_to_visit:
                    runtimes_to_visit.remove(executor)

    assert len(runtimes_to_visit) == 0


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
async def test_deployment_without_replicas_with_sharding(deployment_without_replicas_with_sharding, polling, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-without-replicas-with-sharding.yml')
    deployment_without_replicas_with_sharding.to_docker_compose_yaml(dump_path)

    with DockerComposeServices(dump_path):
        resp = await run_test(
            port=deployment_without_replicas_with_sharding.port, endpoint='/debug', num_docs=10, request_size=1
        )

    assert len(resp) == 10
    docs = resp[0].docs
    for r in resp[1:]:
        docs.extend(r.docs)
    assert len(docs) == 10

    runtimes_to_visit = {
        'test_executor_sharding-0',
        'test_executor_sharding-1',
    }

    for doc in docs:
        if polling == 'ALL':
            assert doc.tags['parallel'] == 1
            assert doc.tags['shards'] == 2
            for executor in doc.tags['traversed-executors']:
                if executor in runtimes_to_visit:
                    runtimes_to_visit.remove(executor)
        else:
            assert doc.tags['parallel'] == 1
            assert doc.tags['shards'] == 2
            for executor in doc.tags['traversed-executors']:
                if executor in runtimes_to_visit:
                    runtimes_to_visit.remove(executor)

    assert len(runtimes_to_visit) == 0


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_deployment_with_replicas_without_sharding(deployment_with_replicas_without_sharding, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-with-replicas-without-sharding.yml')
    deployment_with_replicas_without_sharding.to_docker_compose_yaml(dump_path)

    with DockerComposeServices(dump_path):
        resp = await run_test(
            port=deployment_with_replicas_without_sharding.port, endpoint='/debug', num_docs=10, request_size=1
        )

    assert len(resp) == 10
    docs = resp[0].docs
    for r in resp[1:]:
        docs.extend(r.docs)
    assert len(docs) == 10

    runtimes_to_visit = {
        'test_executor_replicas/rep-0',
        'test_executor_replicas/rep-1',
    }

    for doc in docs:
        assert len(set(doc.tags['traversed-executors'])) == 1
        assert doc.tags['parallel'] == 2
        assert doc.tags['shards'] == 1
        for executor in doc.tags['traversed-executors']:
            if executor in runtimes_to_visit:
                runtimes_to_visit.remove(executor)

    assert len(runtimes_to_visit) == 0


@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_deployment_without_replicas_without_sharding(deployment_without_replicas_without_sharding, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-without-replicas-without-sharding.yml')
    deployment_without_replicas_without_sharding.to_docker_compose_yaml(dump_path)

    with DockerComposeServices(dump_path):
        resp = await run_test(
            port=deployment_without_replicas_without_sharding.port, endpoint='/debug', num_docs=10, request_size=1
        )

    assert len(resp) == 10
    docs = resp[0].docs
    for r in resp[1:]:
        docs.extend(r.docs)
    assert len(docs) == 10

    runtimes_to_visit = {
        'test_executor',
    }

    for doc in docs:
        assert len(set(doc.tags['traversed-executors'])) == 1
        assert doc.tags['parallel'] == 1
        assert doc.tags['shards'] == 1
        for executor in doc.tags['traversed-executors']:
            if executor in runtimes_to_visit:
                runtimes_to_visit.remove(executor)

    assert len(runtimes_to_visit) == 0



@pytest.mark.timeout(3600)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'docker_images', [['test-executor', 'jinaai/jina']], indirect=True
)
async def test_deployment_with_configmap(deployment_configmap, docker_images, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-configmap.yml')
    deployment_configmap.to_docker_compose_yaml(dump_path)

    with DockerComposeServices(dump_path):
        resp = await run_test(
            port=deployment_configmap.port,
            endpoint='/env',
        )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['k1'] == 'v1'
        assert doc.tags['k2'] == 'v2'
        assert doc.tags['env'] == {'k1': 'v1', 'k2': 'v2'}


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'jinaai/jina']],
    indirect=True,
)
async def test_deployment_with_workspace(logger, docker_images, tmpdir):
    port = random_port()
    deployment = Deployment(
        port=port,
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        workspace='/shared',
    )

    dump_path = os.path.join(str(tmpdir), 'docker-compose-deployment-workspace.yml')
    deployment.to_docker_compose_yaml(dump_path)

    with DockerComposeServices(dump_path):
        resp = await run_test(
            port=deployment.port,
            endpoint='/workspace',
        )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['workspace'] == '/shared/TestExecutor/0'


async def test_deployment_http_composite():
    pass
