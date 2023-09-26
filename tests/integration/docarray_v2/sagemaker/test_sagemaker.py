import os
import time
from contextlib import AbstractContextManager

import pytest
import requests

from jina import Deployment
from jina.orchestrate.pods import Pod
from jina.parsers import set_pod_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


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


def test_provider_sagemaker_pod_inference():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        args, _ = set_pod_parser().parse_known_args(
            [
                '--uses',
                'config.yml',
                '--provider',
                'sagemaker',
                'serve',  # This is added by sagemaker
            ]
        )
        with Pod(args):
            # provider=sagemaker would set the port to 8080
            port = 8080
            # Test the `GET /ping` endpoint (added by jina for sagemaker)
            resp = requests.get(f'http://localhost:{port}/ping')
            assert resp.status_code == 200
            assert resp.json() == {}

            # Test the `POST /invocations` endpoint for inference
            # Note: this endpoint is not implemented in the sample executor
            resp = requests.post(
                f'http://localhost:{port}/invocations',
                json={
                    'data': [
                        {'text': 'hello world'},
                    ]
                },
            )
            assert resp.status_code == 200
            resp_json = resp.json()
            assert len(resp_json['data']) == 1
            assert len(resp_json['data'][0]['embeddings'][0]) == 64


def test_provider_sagemaker_pod_batch_transform_valid():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        args, _ = set_pod_parser().parse_known_args(
            [
                '--uses',
                'config.yml',
                '--provider',
                'sagemaker',
                'serve',  # This is added by sagemaker
            ]
        )
        with Pod(args):
            # provider=sagemaker would set the port to 8080
            port = 8080
            # Test `POST /invocations` endpoint for batch-transform with valid input
            with open(
                os.path.join(os.path.dirname(__file__), 'valid_input.csv'), 'r'
            ) as f:
                csv_data = f.read()

            resp = requests.post(
                f'http://localhost:{port}/invocations',
                headers={
                    'accept': 'application/json',
                    'content-type': 'text/csv',
                },
                data=csv_data,
            )
            assert resp.status_code == 200
            resp_json = resp.json()
            assert len(resp_json['data']) == 10
            for d in resp_json['data']:
                assert len(d['embeddings'][0]) == 64


def test_provider_sagemaker_pod_batch_transform_invalid():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        args, _ = set_pod_parser().parse_known_args(
            [
                '--uses',
                'config.yml',
                '--provider',
                'sagemaker',
                'serve',  # This is added by sagemaker
            ]
        )
        with Pod(args):
            # provider=sagemaker would set the port to 8080
            port = 8080
            # Test `POST /invocations` endpoint for batch-transform with invalid input
            with open(
                os.path.join(os.path.dirname(__file__), 'invalid_input.csv'), 'r'
            ) as f:
                csv_data = f.read()

            resp = requests.post(
                f'http://localhost:{port}/invocations',
                headers={
                    'accept': 'application/json',
                    'content-type': 'text/csv',
                },
                data=csv_data,
            )
            assert resp.status_code == 400
            assert (
                resp.json()['detail']
                == "Invalid CSV format. Line ['abcd'] doesn't match the expected field "
                "order ['id', 'text']."
            )


def test_provider_sagemaker_deployment_inference():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        dep_port = 12345
        with Deployment(uses='config.yml', provider='sagemaker', port=dep_port):
            # Test the `GET /ping` endpoint (added by jina for sagemaker)
            rsp = requests.get(f'http://localhost:{dep_port}/ping')
            assert rsp.status_code == 200
            assert rsp.json() == {}

            # Test the `POST /invocations` endpoint
            # Note: this endpoint is not implemented in the sample executor
            rsp = requests.post(
                f'http://localhost:{dep_port}/invocations',
                json={
                    'data': [
                        {'text': 'hello world'},
                    ]
                },
            )
            assert rsp.status_code == 200
            resp_json = rsp.json()
            assert len(resp_json['data']) == 1
            assert len(resp_json['data'][0]['embeddings'][0]) == 64


def test_provider_sagemaker_deployment_inference_docker(replica_docker_image_built):
    with Deployment(uses='docker://sampler-executor', provider='sagemaker', port=12345):
        # Test the `GET /ping` endpoint (added by jina for sagemaker)
        rsp = requests.get('http://localhost:12345/ping')
        assert rsp.status_code == 200
        assert rsp.json() == {}

        # Test the `POST /invocations` endpoint
        # Note: this endpoint is not implemented in the sample executor
        rsp = requests.post(
            'http://localhost:12345/invocations',
            json={
                'data': [
                    {'text': 'hello world'},
                ]
            },
        )
        assert rsp.status_code == 200
        resp_json = rsp.json()
        assert len(resp_json['data']) == 1
        assert len(resp_json['data'][0]['embeddings'][0]) == 64


@pytest.mark.skip('Sagemaker with Deployment for batch-transform is not supported yet')
def test_provider_sagemaker_deployment_batch():
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        dep_port = 12345
        with Deployment(uses='config.yml', provider='sagemaker', port=dep_port):
            # Test the `POST /invocations` endpoint for batch-transform
            with open(
                os.path.join(os.path.dirname(__file__), 'valid_input.csv'), 'r'
            ) as f:
                csv_data = f.read()

            rsp = requests.post(
                f'http://localhost:{dep_port}/invocations',
                headers={
                    'accept': 'application/json',
                    'content-type': 'text/csv',
                },
                data=csv_data,
            )
            assert rsp.status_code == 200
            resp_json = rsp.json()
            assert len(resp_json['data']) == 10
            for d in resp_json['data']:
                assert len(d['embeddings'][0]) == 64


def test_provider_sagemaker_deployment_wrong_port():
    # Sagemaker executor would start on 8080.
    # If we use the same port for deployment, it should raise an error.
    with chdir(os.path.join(os.path.dirname(__file__), 'SampleExecutor')):
        with pytest.raises(ValueError):
            with Deployment(uses='config.yml', provider='sagemaker', port=8080):
                pass
