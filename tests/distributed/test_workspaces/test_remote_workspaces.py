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


@pytest.mark.parametrize('parallels', [1, 2])
def test_upload_via_pymodule(parallels, mocker):
    from .mwu_encoder import MWUEncoder

    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses=MWUEncoder,
            uses_with={'greetings': 'hi'},
            host=CLOUD_HOST,
            parallel=parallels,
            py_modules=['mwu_encoder.py'],
        )
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_upload_via_yaml(parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses='mwu_encoder.yml',
            host=CLOUD_HOST,
            parallel=parallels,
            upload_files=['mwu_encoder.py'],
        )
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [2])
def test_upload_multiple_workspaces(parallels, mocker):
    response_mock = mocker.Mock()
    encoder_workspace = 'sklearn_encoder_ws'
    indexer_workspace = 'tdb_indexer_ws'

    def _path(dir, filename):
        return os.path.join(cur_dir, dir, filename)

    f = (
        Flow()
        .add(
            name='sklearn_encoder',
            uses=_path(encoder_workspace, 'sklearn.yml'),
            host=CLOUD_HOST,
            parallel=parallels,
            py_modules=[_path(encoder_workspace, 'encoder.py')],
            upload_files=[
                _path(encoder_workspace, '.jinad'),
                _path(encoder_workspace, 'requirements.txt'),
            ],
        )
        .add(
            name='tdb_indexer',
            uses=_path(indexer_workspace, 'tdb.yml'),
            host=CLOUD_HOST,
            parallel=parallels,
            py_modules=[_path(indexer_workspace, 'tdb_indexer.py')],
            upload_files=[
                _path(indexer_workspace, '.jinad'),
                _path(indexer_workspace, 'requirements.txt'),
            ],
        )
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


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
def test_upload_simple_non_standard_rootworkspace(docker_compose, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses='mwu_encoder.yml',
            host='localhost:9000',
            upload_files=['mwu_encoder.py'],
        )
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()
