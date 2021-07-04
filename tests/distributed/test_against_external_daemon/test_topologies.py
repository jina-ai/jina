import os

import pytest

from jina import Flow, Document

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
@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(
            host=CLOUD_HOST,
            parallel=parallels,
            quiet_remote_logs=silent_log,
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
def test_l_r_simple(parallels, mocker):
    response_mock = mocker.Mock()

    f = Flow().add(parallel=parallels).add(host=CLOUD_HOST, parallel=parallels)
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_r_l_r_simple(parallels, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(host=CLOUD_HOST, parallel=parallels)
        .add()
        .add(host=CLOUD_HOST, parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_r_r_r_simple(parallels, mocker):
    response_mock = mocker.Mock()

    f = (
        Flow()
        .add(host=CLOUD_HOST, parallel=parallels)
        .add(host=CLOUD_HOST, parallel=parallels)
        .add(host=CLOUD_HOST, parallel=parallels)
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.parametrize('parallels', [1, 2])
def test_l_r_l_simple(parallels, mocker):
    response_mock = mocker.Mock()

    f = Flow().add().add(host=CLOUD_HOST, parallel=parallels).add()
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.skip('not tested')
@pytest.mark.parametrize('parallels', [1, 2])
def test_needs(parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(name='pod1', parallel=parallels)
        .add(host=CLOUD_HOST, name='pod2', parallel=parallels, needs='gateway')
        .add(name='pod3', parallel=parallels, needs=['pod1'])
        .needs_all()
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()


@pytest.mark.skip('not tested')
@pytest.mark.parametrize('parallels', [1, 2])
def test_complex_needs(parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add(name='r1')
        .add(name='r2', host=CLOUD_HOST)
        .add(name='r3', needs='r1', host=CLOUD_HOST, parallel=parallels)
        .add(name='r4', needs='r2', parallel=parallels)
        .add(name='r5', needs='r3')
        .add(name='r6', needs='r4', host=CLOUD_HOST)
        .add(name='r8', needs='r6', parallel=parallels)
        .add(name='r9', needs='r5', host=CLOUD_HOST, parallel=parallels)
        .add(name='r10', needs=['r9', 'r8'])
    )
    with f:
        f.index(
            inputs=(Document(text='hello') for _ in range(NUM_DOCS)),
            on_done=response_mock,
        )
    response_mock.assert_called()
