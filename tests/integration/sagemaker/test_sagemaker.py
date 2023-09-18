import os
from contextlib import AbstractContextManager

import requests

from jina.orchestrate.pods import Pod
from jina.parsers import set_pod_parser


class chdir(AbstractContextManager):
    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())


def test_provider_sagemaker():
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
            rsp = requests.get(f'http://localhost:{port}/ping')
            assert rsp.status_code == 200
            assert rsp.json() == {}

            # Test the `POST /invocations` endpoint
            # Note: this endpoint is not implemented in the sample executor
            rsp = requests.post(
                f'http://localhost:{port}/invocations',
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
