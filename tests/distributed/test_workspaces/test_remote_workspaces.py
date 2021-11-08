import os
import time
import asyncio

import numpy as np
import pytest

from jina.enums import RemoteWorkspaceState
from jina import Flow, Client, Document, __default_host__
from daemon.models.id import DaemonID
from daemon.models.workspaces import WorkspaceItem
from daemon.clients import JinaDClient, AsyncJinaDClient
from ..helpers import assert_request

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

"""
Run below commands for local tests
docker build --build-arg PIP_TAG=daemon -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .
docker run --add-host host.docker.internal:host-gateway \
    --name jinad -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/jinad:/tmp/jinad \
    -p 8000:8000 -d jinaai/jina:test-daemon
"""

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.mark.parametrize('replicas', [1, 2])
def test_upload_via_pymodule(replicas):
    from .mwu_encoder import MWUEncoder

    f = (
        Flow()
        .add()
        .add(
            uses=MWUEncoder,
            uses_with={'greetings': 'hi'},
            host=CLOUD_HOST,
            replicas=replicas,
            py_modules='mwu_encoder.py',
            upload_files=cur_dir,
        )
        .add()
    )
    with f:
        responses = f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            return_results=True,
        )
    assert len(responses) > 0
    assert len(responses[0].docs) > 0
    for doc in responses[0].docs:
        assert doc.tags['greetings'] == 'hi'


@pytest.mark.parametrize('replicas', [1, 2])
def test_upload_via_yaml(replicas):
    f = (
        Flow()
        .add()
        .add(
            uses='mwu_encoder.yml',
            host=CLOUD_HOST,
            replicas=replicas,
            upload_files=cur_dir,
        )
        .add()
    )
    with f:
        responses = f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            return_results=True,
        )
    assert len(responses) > 0
    assert len(responses[0].docs) > 0


@pytest.mark.parametrize('replicas', [2])
def test_upload_multiple_workspaces(replicas):
    encoder_workspace = 'sklearn_encoder_ws'
    indexer_workspace = 'tdb_indexer_ws'

    f = (
        Flow()
        .add(
            name='sklearn_encoder',
            uses='sklearn.yml',
            host=CLOUD_HOST,
            replicas=replicas,
            py_modules='encoder.py',
            upload_files=encoder_workspace,
        )
        .add(
            name='tdb_indexer',
            uses='tdb.yml',
            host=CLOUD_HOST,
            replicas=replicas,
            py_modules='tdb_indexer.py',
            upload_files=indexer_workspace,
        )
    )
    with f:
        responses = f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            return_results=True,
        )
    assert len(responses) > 0
    assert len(responses[0].docs) > 0


def test_remote_flow():
    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(
        paths=[os.path.join(cur_dir, 'empty_flow.yml')]
    )
    assert DaemonID(workspace_id).type == 'workspace'
    flow_id = client.flows.create(workspace_id=workspace_id, filename='empty_flow.yml')
    assert DaemonID(flow_id).type == 'flow'
    assert client.flows.get(flow_id)
    assert flow_id in client.flows.list()
    assert_request('get', url=f'http://localhost:23456/status/', expect_rcode=200)
    assert client.flows.delete(flow_id)
    assert client.workspaces.delete(workspace_id)


def test_workspace_delete():
    client = JinaDClient(host=__default_host__, port=8000)
    for _ in range(2):
        workspace_id = client.workspaces.create(
            paths=[os.path.join(cur_dir, 'empty_flow.yml')]
        )
        assert DaemonID(workspace_id).type == 'workspace'
        assert (
            WorkspaceItem(**client.workspaces.get(id=workspace_id)).state
            == RemoteWorkspaceState.ACTIVE
        )
        assert workspace_id in client.workspaces.list()
        assert client.workspaces.delete(workspace_id)


def test_workspace_clear():
    client = JinaDClient(host=__default_host__, port=8000)
    for _ in range(2):
        workspace_id = client.workspaces.create(
            paths=[os.path.join(cur_dir, 'empty_flow.yml')]
        )
        assert DaemonID(workspace_id).type == 'workspace'
        assert (
            WorkspaceItem(**client.workspaces.get(id=workspace_id)).state
            == RemoteWorkspaceState.ACTIVE
        )
        assert workspace_id in client.workspaces.list()
        assert client.workspaces.clear()


@pytest.mark.asyncio
async def test_custom_project():

    HOST = __default_host__

    client = AsyncJinaDClient(host=HOST, port=8000)
    workspace_id = await client.workspaces.create(
        paths=[os.path.join(cur_dir, 'flow_app_ws')]
    )
    assert DaemonID(workspace_id).type == 'workspace'
    # Sleep to allow the workspace container to start
    await asyncio.sleep(20)

    async def gen_docs():
        import string

        d = iter(string.ascii_lowercase)
        while True:
            try:
                yield Document(tags={'first': next(d), 'second': next(d)})
            except StopIteration:
                return

    async for resp in Client(
        asyncio=True, host=HOST, port=42860, show_progress=True
    ).post(on='/index', inputs=gen_docs):
        pass

    async for resp in Client(
        asyncio=True, host=HOST, port=42860, show_progress=True
    ).post(
        on='/search',
        inputs=Document(tags={'key': 'first', 'value': 's'}),
        return_results=True,
    ):
        fields = resp.data.docs[0].matches[0].tags.fields
        assert fields['first'].string_value == 's'
        assert fields['second'].string_value == 't'
    print(f'Deleting workspace {workspace_id}')
    assert await client.workspaces.delete(workspace_id)


@pytest.fixture()
def docker_compose(request):
    os.system(f'docker network prune -f ')
    os.system(
        f'docker-compose -f {request.param} --project-directory . up  --build -d --remove-orphans'
    )
    time.sleep(5)
    yield
    os.system(
        f'docker-compose -f {request.param} --project-directory . down --remove-orphans'
    )
    os.system(f'docker network prune -f ')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_upload_simple_non_standard_rootworkspace(docker_compose):
    f = (
        Flow()
        .add()
        .add(
            uses='mwu_encoder.yml',
            host='localhost:9000',
            upload_files=cur_dir,
        )
        .add()
    )
    with f:
        responses = f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            return_results=True,
        )
    assert len(responses) > 0
    assert len(responses[0].docs) > 0
