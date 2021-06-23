import ipaddress
import os
import time

import docker
import numpy as np
import pytest
import requests

from jina import Flow, Client, Document, __default_host__
from ..helpers import create_workspace, wait_for_workspace, delete_workspace, _jinad_url

cur_dir = os.path.dirname(os.path.abspath(__file__))

"""
Run below commands for local tests
docker build -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .
docker run --add-host host.docker.internal:host-gateway \
    --name jinad -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/jinad:/tmp/jinad \
    -p 8000:8000 -d jinaai/jina:test-daemon
"""

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
NUM_DOCS = 100


@pytest.mark.parametrize('silent_log', [False])
@pytest.mark.parametrize('parallels', [1])
def test_upload_simple(silent_log, parallels, mocker):
    response_mock = mocker.Mock()
    f = (
        Flow()
        .add()
        .add(
            uses='mwu_encoder.yml',
            host=CLOUD_HOST,
            parallel=parallels,
            upload_files=['mwu_encoder.py'],
            quiet_remote_logs=silent_log,
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
    encoder_workspace = 'tf_encoder_ws'
    indexer_workspace = 'tdb_indexer_ws'

    def _path(dir, filename):
        return os.path.join(cur_dir, dir, filename)

    f = (
        Flow()
        .add(
            name='tf_encoder',
            uses=_path(encoder_workspace, 'tf.yml'),
            host=CLOUD_HOST,
            parallel=parallels,
            py_modules=[_path(encoder_workspace, 'tf_encoder.py')],
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


def test_custom_project():

    HOST = __default_host__

    workspace_id = create_workspace(
        dirpath=os.path.join(cur_dir, 'flow_app_ws'), host=HOST
    )
    assert wait_for_workspace(workspace_id, host=HOST)
    # we need to wait for the flow to start in the custom project
    time.sleep(5)

    def gen_docs():
        import string

        d = iter(string.ascii_lowercase)
        while True:
            try:
                yield Document(tags={'first': next(d), 'second': next(d)})
            except StopIteration:
                return

    Client(host=HOST, port_expose=42860, show_progress=True).post(
        on='/index', inputs=gen_docs
    )
    res = Client(host=HOST, port_expose=42860, show_progress=True).post(
        on='/search',
        inputs=Document(tags={'key': 'first', 'value': 's'}),
        return_results=True,
    )
    assert res[0].data.docs[0].matches[0].tags.fields['first'].string_value == 's'
    assert res[0].data.docs[0].matches[0].tags.fields['second'].string_value == 't'
    delete_workspace(workspace_id, host=HOST)


def test_multiple_workspaces_networks():
    workspace_id_1 = create_workspace(dirpath=os.path.join(cur_dir, 'flow_app_ws'))
    assert wait_for_workspace(workspace_id_1)
    workspace_id_2 = create_workspace(
        filepaths=[os.path.join(cur_dir, 'blocking.jinad')]
    )
    assert wait_for_workspace(workspace_id_2)

    client = docker.from_env()
    docker_network1 = client.networks.get(_get_network(workspace_id_1))
    docker_network2 = client.networks.get(_get_network(workspace_id_2))

    network1 = ipaddress.ip_network(
        docker_network1.attrs['IPAM']['Config'][0]['Subnet']
    )
    network2 = ipaddress.ip_network(
        docker_network2.attrs['IPAM']['Config'][0]['Subnet']
    )
    assert not network1.overlaps(network2)

    delete_workspace(workspace_id_1)
    delete_workspace(workspace_id_2)


def _get_network(workspace_id):
    url = _jinad_url(__default_host__, 8000, 'workspaces')
    r = requests.get(f'{url}/{workspace_id}')
    return r.json()['metadata']['network']


def test_multiple_workspaces_networks_after_restart():
    client = docker.from_env()
    workspace_id_1 = create_workspace(dirpath=os.path.join(cur_dir, 'flow_app_ws'))
    assert wait_for_workspace(workspace_id_1)

    # restart jinad
    _restart_external_jinad(client)

    workspace_id_2 = create_workspace(
        filepaths=[os.path.join(cur_dir, 'blocking.jinad')]
    )
    assert wait_for_workspace(workspace_id_2)

    docker_network1 = client.networks.get(_get_network(workspace_id_1))
    docker_network2 = client.networks.get(_get_network(workspace_id_2))

    network1 = ipaddress.ip_network(
        docker_network1.attrs['IPAM']['Config'][0]['Subnet']
    )
    network2 = ipaddress.ip_network(
        docker_network2.attrs['IPAM']['Config'][0]['Subnet']
    )
    assert not network1.overlaps(network2)

    delete_workspace(workspace_id_1)
    delete_workspace(workspace_id_2)


def _restart_external_jinad(client):
    containers = client.containers.list()
    for container in containers:
        if container.name == 'jinad':
            container.restart()
            time.sleep(5.0)
            return
