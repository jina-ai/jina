import os

import pytest
import numpy as np

from daemon.clients import JinaDClient
from daemon import __partial_workspace__
from jina import Flow, Document, Client, __default_host__

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


@pytest.mark.parametrize('silent_log', [True, False])
@pytest.mark.parametrize('replicas', [1, 2])
def test_r_l_simple(silent_log, replicas, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(
            host=CLOUD_HOST,
            replicas=replicas,
            quiet_remote_logs=silent_log,
            timeout_ready=-1,
        )
        .add(replicas=replicas)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
            show_progress=True,
        )

    response_mock.assert_called()


@pytest.mark.parametrize('replicas', [1, 2])
def test_l_r_simple(replicas, mocker):
    response_mock = mocker.Mock()

    f = Flow().add(replicas=replicas).add(host=CLOUD_HOST, replicas=replicas)
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
            show_progress=True,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('replicas', [1, 2])
def test_r_l_r_simple(replicas, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(host=CLOUD_HOST, replicas=replicas)
        .add()
        .add(host=CLOUD_HOST, replicas=replicas)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
            show_progress=True,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('replicas', [1, 2])
def test_r_r_r_simple(replicas, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(host=CLOUD_HOST, replicas=replicas)
        .add(host=CLOUD_HOST, replicas=replicas)
        .add(host=CLOUD_HOST, replicas=replicas)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
            show_progress=True,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('replicas', [1, 2])
def test_l_r_l_simple(replicas, mocker):
    response_mock = mocker.Mock()

    f = Flow().add().add(host=CLOUD_HOST, replicas=replicas).add()
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
            show_progress=True,
        )
    response_mock.assert_called()


@pytest.mark.skip('not tested')
@pytest.mark.parametrize('replicas', [1, 2])
def test_needs(replicas, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(name='executor1', replicas=replicas)
        .add(host=CLOUD_HOST, name='executor2', replicas=replicas, needs='gateway')
        .add(name='executor3', replicas=replicas, needs=['executor1'])
        .needs_all()
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.skip('not tested')
@pytest.mark.parametrize('replicas', [1, 2])
def test_complex_needs(replicas, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(name='r1')
        .add(name='r2', host=CLOUD_HOST)
        .add(name='r3', needs='r1', host=CLOUD_HOST, replicas=replicas)
        .add(name='r4', needs='r2', replicas=replicas)
        .add(name='r5', needs='r3')
        .add(name='r6', needs='r4', host=CLOUD_HOST)
        .add(name='r8', needs='r6', replicas=replicas)
        .add(name='r9', needs='r5', host=CLOUD_HOST, replicas=replicas)
        .add(name='r10', needs=['r9', 'r8'])
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('replicas', [1, 2])
def test_remote_flow_local_executors(mocker, replicas):

    client = JinaDClient(host=__default_host__, port=8000)
    workspace_id = client.workspaces.create(paths=[os.path.join(cur_dir, 'yamls')])

    GATEWAY_LOCAL_GATEWAY = 'flow_glg.yml'
    GATEWAY_LOCAL_LOCAL_GATEWAY = 'flow_gllg.yml'

    for flow_yaml in [
        GATEWAY_LOCAL_GATEWAY,
        GATEWAY_LOCAL_LOCAL_GATEWAY,
    ]:
        response_mock = mocker.Mock()
        flow_id = client.flows.create(
            workspace_id=workspace_id, filename=flow_yaml, envs={'REPLICAS': replicas}
        )
        args = client.flows.get(flow_id)['arguments']['object']['arguments']
        Client(
            host=__default_host__,
            port=args['port_expose'],
            protocol=args['protocol'],
        ).post(
            on='/',
            inputs=(Document(blob=np.random.random([1, 100])) for _ in range(NUM_DOCS)),
            on_done=response_mock,
            show_progress=True,
        )
        response_mock.assert_called()
        assert client.flows.delete(flow_id)

    assert client.workspaces.delete(workspace_id)


def test_remote_workspace_value():
    """
    This tests the value set in `self.workspace` in a remote Flow.
    It should always be `/workspace/ExecutorName/...
    """
    HOST = __default_host__
    client = JinaDClient(host=HOST, port=8000)
    workspace_id = client.workspaces.create(paths=[os.path.join(cur_dir, 'yamls')])
    flow_id = client.flows.create(
        workspace_id=workspace_id, filename='flow_workspace_validate.yml'
    )
    args = client.flows.get(flow_id)['arguments']['object']['arguments']
    response = Client(
        host=HOST, port=args['port_expose'], protocol=args['protocol']
    ).post(on='/', inputs=[Document()], show_progress=True, return_results=True)
    assert (
        response[0]
        .data.docs[0]
        .text.startswith(f'{__partial_workspace__}/WorkspaceValidator/0')
    )
    assert client.flows.delete(flow_id)
    assert client.workspaces.delete(workspace_id)


@pytest.mark.parametrize('gpus', ['all', '2'])
def test_remote_executor_gpu(mocker, gpus):
    # This test wouldn't be able to use gpus on remote, as they're not available on CI.
    # But it shouldn't fail the Pea creation.
    response_mock = mocker.Mock()
    f = Flow().add(host=CLOUD_HOST, gpus=gpus)
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()
