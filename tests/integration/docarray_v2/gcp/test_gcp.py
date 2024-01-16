import csv
import io
import os
import time
from contextlib import AbstractContextManager

import pytest
import requests

from jina import Deployment
from jina.helper import random_port
from jina.orchestrate.pods import Pod
from jina.parsers import set_pod_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))
gcp_port = 8080


@pytest.fixture
def replica_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=cur_dir, tag='sampler-executor')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


class chdir(AbstractContextManager):
    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())


def test_provider_gcp_pod_inference():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        args, _ = set_pod_parser().parse_known_args(
            [
                '--uses',
                'config.yml',
                '--provider',
                'gcp',
                'serve',  # This is added by gcp
            ]
        )
        with Pod(args):
            # Test the `GET /ping` endpoint (added by jina for gcp)
            resp = requests.get(f'http://localhost:{gcp_port}/ping')
            assert resp.status_code == 200
            assert resp.json() == {}

            # Test the `POST /invocations` endpoint for inference
            # Note: this endpoint is not implemented in the sample executor
            resp = requests.post(
                f'http://localhost:{gcp_port}/invocations',
                json={
                    'instances': ["hello world", "good apple"]
                },
            )
            assert resp.status_code == 200
            resp_json = resp.json()
            assert len(resp_json['predictions']) == 2


def test_provider_gcp_deployment_inference():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        dep_port = random_port()
        with Deployment(uses='config.yml', provider='gcp', port=dep_port):
            # Test the `GET /ping` endpoint (added by jina for gcp)
            resp = requests.get(f'http://localhost:{dep_port}/ping')
            assert resp.status_code == 200
            assert resp.json() == {}

            # Test the `POST /invocations` endpoint
            # Note: this endpoint is not implemented in the sample executor
            resp = requests.post(
                f'http://localhost:{dep_port}/invocations',
                json={
                    'instances': ["hello world", "good apple"]
                },
            )
            assert resp.status_code == 200
            resp_json = resp.json()
            assert len(resp_json['predictions']) == 2
