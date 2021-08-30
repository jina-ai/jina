import os

import numpy as np
import pytest

from daemon.clients import JinaDClient
from jina import Flow, Client, Document, __default_host__


cur_dir = os.path.dirname(os.path.abspath(__file__))

"""
Run below commands for local tests
docker build --build-arg PIP_TAG=daemon -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .
docker run --add-host host.docker.internal:host-gateway \
    --name jinad -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/jinad:/tmp/jinad \
    -p 8000:8000 -d jinaai/jina:test-daemon
"""

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.fixture()
def docker_image():
    img_name = 'test-mwu-encoder'
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'mwu-encoder/'), tag=img_name)
    client.close()
    yield img_name
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_docker(parallels, docker_image, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(
            uses=f'docker://{docker_image}',
            host=CLOUD_HOST,
            parallel=parallels,
            timeout_ready=-1,
        )
        .add(parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )

    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_docker(parallels, docker_image, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(parallel=parallels)
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_r_docker(parallels, docker_image, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
        .add()
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1])
def test_r_r_r_docker(parallels, docker_image, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_l_docker(parallels, docker_image, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(uses=f'docker://{docker_image}', host=CLOUD_HOST, parallel=parallels)
        .add()
    )
    with f:
        f.index(
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


def test_remote_flow_containerized_executors(docker_image, mocker):
    response_mock = mocker.Mock()
    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(paths=[os.path.join(cur_dir, 'yamls')])

    GATEWAY_CONTAINER_GATEWAY = 'flow_gcg.yml'
    GATEWAY_CONTAINER_LOCAL_GATEWAY = 'flow_gclg.yml'
    GATEWAY_LOCAL_CONTAINER_GATEWAY = 'flow_gclg.yml'
    GATEWAY_CONTAINER_LOCAL_CONTAINER_GATEWAY = 'flow_gclcg.yml'

    for flow_yaml in [
        GATEWAY_CONTAINER_GATEWAY,
        GATEWAY_CONTAINER_LOCAL_GATEWAY,
        GATEWAY_LOCAL_CONTAINER_GATEWAY,
        GATEWAY_CONTAINER_LOCAL_CONTAINER_GATEWAY,
    ]:
        flow_id = client.flows.create(workspace_id=workspace_id, filename=flow_yaml)
        args = client.flows.get(flow_id)['arguments']['object']['arguments']
        Client(
            host=__default_host__,
            port=args['port_expose'],
            protocol=args['protocol'],
        ).post(
            on='/',
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
        response_mock.assert_called()
        assert client.flows.delete(flow_id)

    assert client.workspaces.delete(workspace_id)
