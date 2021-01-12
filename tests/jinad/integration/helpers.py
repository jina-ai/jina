import json
from pathlib import Path
from contextlib import ExitStack
from typing import Optional, Dict

import requests


def invoke_requests(method: str,
                    url: str,
                    payload: Optional[Dict] = None,
                    headers: Dict = {'Content-Type': 'application/json'}):
    try:
        response = getattr(requests, method)(
            url, data=json.dumps(payload), headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'got an exception while invoking request {e!r}')
        return

def get_results(query: str,
                url: str = 'http://0.0.0.0:45678/api/search',
                method: str = 'post',
                top_k: int = 10):
    return invoke_requests(method=method,
                           url=url,
                           payload={'top_k': top_k, 'data': [query]})


def create_flow(flow_yaml: str,
                pod_dir: Optional[str] = None,
                url: str = 'http://localhost:8000/flow/yaml'):
    with ExitStack() as file_stack:
        pymodules_files = []
        uses_files = []
        if pod_dir is not None:
            uses_files = [
                ('uses_files', file_stack.enter_context(open(file_path)))
                for file_path in Path(pod_dir).glob('*.yml')
            ]
            pymodules_files = [
                ('pymodules_files', file_stack.enter_context(open(file_path)))
                for file_path in Path(pod_dir).rglob('*.py')
            ]

        files = [
            *uses_files,
            *pymodules_files,
            ('yamlspec', file_stack.enter_context(open(flow_yaml))),
        ]
        response = requests.put(url, files=files)
        print('Checking if the flow creation succeeded -- ')
        assert response.status_code == 200
        return response.json()
