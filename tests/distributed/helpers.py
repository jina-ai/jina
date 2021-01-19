from contextlib import ExitStack
from pathlib import Path
from typing import Optional, Dict

import requests


def invoke_requests(method: str,
                    url: str,
                    payload: Optional[Dict] = None):
    try:
        response = getattr(requests, method)(
            url, json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'got an exception while invoking request {e!r}')


def get_results(query: str,
                url: str = 'http://0.0.0.0:45678/api/search',
                method: str = 'post',
                top_k: int = 10):
    return invoke_requests(method=method,
                           url=url,
                           payload={'top_k': top_k, 'data': [query]})


def create_flow(flow_yaml: str,
                pod_dir: Optional[str] = None,
                url: str = 'http://localhost:8000'):
    with ExitStack() as file_stack:
        pymodules_files = []
        uses_files = []
        if pod_dir is not None:
            uses_files = [
                ('files', file_stack.enter_context(open(file_path, 'rb')))
                for file_path in Path(pod_dir).glob('*.yml')
            ]
            pymodules_files = [
                ('files', file_stack.enter_context(open(file_path, 'rb')))
                for file_path in Path(pod_dir).rglob('*.py')
            ]

        files = [
            *uses_files,
            *pymodules_files,
        ]
        print(f'will upload {files}')
        r = requests.post(f'{url}/workspaces', files=files)
        print(f'Checking if the upload is succeeded: {r.json()}')
        assert r.status_code == 200
        workspace_id = r.json()
        r = requests.post(f'{url}/flows',
                          files={'flow': ('good_flow.yml', file_stack.enter_context(open(flow_yaml, 'rb'))),
                                 'workspace_id': (None, workspace_id)})
        print(f'Checking if the flow creation is succeeded: {r.json()}')
        assert r.status_code == 201
        return r
