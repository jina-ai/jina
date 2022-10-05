import os
import time

import pytest
from docarray import Document, DocumentArray

from jina import Flow
from jina.helper import random_port
from jina.orchestrate.deployments import Deployment
from jina.parsers import set_deployment_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def replica_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=cur_dir, tag='worker-runtime')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.fixture(scope='function')
def input_docs():
    return DocumentArray([Document() for _ in range(50)])


def _external_deployment_args(num_shards, port=None):
    args = [
        '--uses',
        os.path.join(cur_dir, 'config.yml'),
        '--name',
        'external_real',
        '--port',
        str(port) if port else str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


def _external_deployment_args_docker(num_shards, port=None):
    args = [
        '--uses',
        'docker://worker-runtime',
        '--name',
        'external_real',
        '--port',
        str(port) if port else str(random_port()),
        '--host-in',
        '0.0.0.0',
        '--shards',
        str(num_shards),
        '--polling',
        'all',
    ]
    return set_deployment_parser().parse_args(args)


@pytest.mark.parametrize('hosts', ['localhost,localhost', 'localhost'])
def test_distributed_replicas(input_docs, hosts):
    port1, port2 = random_port(), random_port()
    args1, args2 = _external_deployment_args(
        num_shards=1, port=port1
    ), _external_deployment_args(num_shards=1, port=port2)
    depl1 = Deployment(args1)
    depl2 = Deployment(args2)
    with depl1, depl2:
        flow = Flow().add(
            host=hosts,
            port=f'{port1},{port2}',
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs, request_size=2)

        depl1_id = resp[0].tags['uuid']
        assert any([depl1_id != depl_id for depl_id in resp[1:, 'tags__uuid']])


@pytest.mark.parametrize('hosts', ['localhost,localhost', 'localhost'])
def test_distributed_replicas_docker(input_docs, hosts, replica_docker_image_built):
    port1, port2 = random_port(), random_port()
    args1, args2 = _external_deployment_args_docker(
        num_shards=1, port=port1
    ), _external_deployment_args_docker(num_shards=1, port=port2)
    depl1 = Deployment(args1)
    depl2 = Deployment(args2)
    with depl1, depl2:
        flow = Flow().add(
            host=hosts,
            port=f'{port1},{port2}',
            external=True,
        )
        with flow:
            resp = flow.index(inputs=input_docs, request_size=2)

        depl1_id = resp[0].tags['uuid']
        assert any([depl1_id != depl_id for depl_id in resp[1:, 'tags__uuid']])
