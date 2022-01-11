# kind version has to be bumped to v0.11.1 since pytest-kind is just using v0.10.0 which does not work on ubuntu in ci
import pytest
import os
import time

from jina import Flow, Document


class DockerComposeFlow:
    def __init__(self, dump_path):
        self.dump_path = dump_path

    def __enter__(self):
        os.system(
            f"docker-compose -f {self.dump_path} --project-directory . up  --build -d --remove-orphans"
        )
        time.sleep(10)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.system(
            f"docker-compose -f {self.dump_path} --project-directory . down --remove-orphans"
        )


async def run_test(flow, endpoint, num_docs=10, request_size=10):
    # start port forwarding
    from jina.clients import Client

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
        endpoint,
        inputs=[Document() for _ in range(num_docs)],
        return_results=True,
        request_size=request_size,
    ):
        responses.append(resp)

    return responses


@pytest.fixture()
def flow_with_sharding(docker_images, polling):
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
def flow_configmap(docker_images):
    flow = Flow(name='k8s-flow-configmap', port_expose=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        env={'k1': 'v1', 'k2': 'v2'},
    )
    return flow


@pytest.fixture
def flow_with_needs(docker_images):
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
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
async def test_flow_with_needs(logger, flow_with_needs, tmpdir, docker_images):
    dump_path = os.path.join(str(tmpdir), 'docker-compose.yml')
    flow_with_needs.to_docker_compose_yaml(dump_path, 'default')
    with DockerComposeFlow(dump_path):
        resp = await run_test(
            flow=flow_with_needs,
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
@pytest.mark.parametrize(
    'docker_images',
    [['test-executor', 'executor-merger', 'jinaai/jina']],
    indirect=True,
)
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
async def test_flow_with_sharding(flow_with_sharding, polling, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose.yml')
    flow_with_sharding.to_docker_compose_yaml(dump_path)

    with DockerComposeFlow(dump_path):
        resp = await run_test(
            flow=flow_with_sharding, endpoint='/debug', num_docs=10, request_size=1
        )

    assert len(resp) == 10
    docs = resp[0].docs
    for r in resp[1:]:
        docs.extend(r.docs)
    assert len(docs) == 10

    runtimes_to_visit = {
        'test_executor-0/rep-0',
        'test_executor-1/rep-0',
        'test_executor-0/rep-1',
        'test_executor-1/rep-1',
    }

    for doc in docs:
        if polling == 'ALL':
            assert len(set(doc.tags['traversed-executors'])) == 2
            assert set(doc.tags['pea_id']) == {0, 1}
            assert set(doc.tags['shard_id']) == {0, 1}
            assert doc.tags['parallel'] == [2, 2]
            assert doc.tags['shards'] == [2, 2]
            for executor in doc.tags['traversed-executors']:
                if executor in runtimes_to_visit:
                    runtimes_to_visit.remove(executor)
        else:
            assert len(set(doc.tags['traversed-executors'])) == 1
            assert len(set(doc.tags['pea_id'])) == 1
            assert len(set(doc.tags['shard_id'])) == 1
            assert 0 in set(doc.tags['pea_id']) or 1 in set(doc.tags['pea_id'])
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
    'docker_images', [['test-executor', 'jinaai/jina']], indirect=True
)
async def test_flow_with_configmap(flow_configmap, docker_images, tmpdir):
    dump_path = os.path.join(str(tmpdir), 'docker-compose.yml')
    flow_configmap.to_docker_compose_yaml(dump_path)

    with DockerComposeFlow(dump_path):
        resp = await run_test(
            flow=flow_configmap,
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
async def test_flow_with_workspace(logger, docker_images, tmpdir):
    flow = Flow(name='k8s_flow-with_workspace', port_expose=9090, protocol='http').add(
        name='test_executor',
        uses=f'docker://{docker_images[0]}',
        workspace='/shared',
    )

    dump_path = os.path.join(str(tmpdir), 'docker-compose.yml')
    flow.to_docker_compose_yaml(dump_path)

    with DockerComposeFlow(dump_path):
        resp = await run_test(
            flow=flow,
            endpoint='/workspace',
        )

    docs = resp[0].docs
    assert len(docs) == 10
    for doc in docs:
        assert doc.tags['workspace'] == '/shared/TestExecutor/0'
