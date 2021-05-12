from contextlib import ExitStack
from pathlib import Path
from typing import List, Optional, Dict

import requests

from jina.parsers import set_client_cli_parser


def assert_request(
    method: str, url: str, payload: Optional[Dict] = None, expect_rcode: int = 200
):
    try:
        if payload:
            response = getattr(requests, method)(url, json=payload)
        else:
            response = getattr(requests, method)(url)
        assert response.status_code == expect_rcode
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'got an exception while invoking request {e!r}')


def get_results(
    query: str,
    url: str = 'http://0.0.0.0:45678/search',
    method: str = 'post',
    top_k: int = 10,
):
    return assert_request(
        method=method, url=url, payload={'top_k': top_k, 'data': [query]}
    )


def create_workspace(
    filepaths: List[str], url: str = 'http://localhost:8000/workspaces'
) -> str:
    with ExitStack() as file_stack:
        files = [
            ('files', file_stack.enter_context(open(filepath, 'rb')))
            for filepath in filepaths
        ]
        print(f'uploading {files}')
        r = requests.post(url, files=files)
        assert r.status_code == 201

        workspace_id = r.json()
        print(f'Got workspace_id: {workspace_id}')
        return workspace_id


def create_flow_2(
    flow_yaml: str,
    workspace_id: Optional[str] = None,
    url: str = 'http://localhost:8000/flows',
) -> str:
    with open(flow_yaml, 'rb') as f:
        r = requests.post(url, data={'workspace_id': workspace_id}, files={'flow': f})
        print(f'Checking if the flow creation is succeeded: {r.json()}')
        assert r.status_code == 201
        return r.json()


def create_flow(
    flow_yaml: str,
    pod_dir: Optional[str] = None,
    url: str = 'http://localhost:8000',
    workspace_id: Optional[str] = None,
) -> str:
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
        if files:
            print(f'will upload {files}')
            r = requests.post(f'{url}/workspaces', files=files)
            print(f'Checking if the upload is succeeded: {r.json()}')
            assert r.status_code == 201
            workspace_id = r.json()

            r = requests.get(f'{url}/workspaces/{workspace_id}')
            print(f'Listing upload files: {r.json()}')
            assert r.status_code == 200
        else:
            print('nothing to upload')

        if workspace_id:
            r = requests.post(
                f'{url}/flows',
                files={
                    'flow': (
                        'good_flow.yml',
                        file_stack.enter_context(open(flow_yaml, 'rb')),
                    ),
                    'workspace_id': (None, workspace_id),
                },
            )
        else:
            r = requests.post(
                f'{url}/flows',
                files={
                    'flow': (
                        'good_flow.yml',
                        file_stack.enter_context(open(flow_yaml, 'rb')),
                    )
                },
            )

        print(f'Checking if the flow creation is succeeded: {r.json()}')
        assert r.status_code == 201
        return r.json()
