import time
from contextlib import ExitStack
from pathlib import Path
from typing import List, Optional, Dict

import requests

from daemon.models import DaemonID
from jina import __default_host__
from jina.enums import RemoteWorkspaceState


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


def _jinad_url(host: str, port: int, kind: str):
    return f'http://{host}:{port}/{kind}'


def create_workspace(
    filepaths: Optional[List[str]] = None,
    dirpath: Optional[str] = None,
    workspace_id: Optional[DaemonID] = None,
    host: str = __default_host__,
    port: int = 8000,
) -> Optional[str]:
    with ExitStack() as file_stack:

        def _to_file_tuple(path):
            return ('files', file_stack.enter_context(open(path, 'rb')))

        files_to_upload = set()
        if filepaths:
            files_to_upload.update([_to_file_tuple(filepath) for filepath in filepaths])
        if dirpath:
            for ext in ['*yml', '*yaml', '*py', '*.jinad', 'requirements.txt']:
                files_to_upload.update(
                    [_to_file_tuple(filepath) for filepath in Path(dirpath).rglob(ext)]
                )

        if not files_to_upload:
            print('nothing to upload')
            return

        print(f'will upload files: {files_to_upload}')
        url = _jinad_url(host, port, 'workspaces')
        r = requests.post(url, files=list(files_to_upload))
        print(f'Checking if the upload is succeeded: {r.json()}')
        assert r.status_code == 201
        json_response = r.json()
        workspace_id = next(iter(json_response))
        return workspace_id


def delete_workspace(
    workspace_id: DaemonID,
    host: str = __default_host__,
    port: int = 8000,
) -> bool:
    print(f'will delete workspace {workspace_id}')
    url = _jinad_url(host, port, f'workspaces/{workspace_id}')
    r = requests.delete(url, params={'everything': True})
    return r.status_code == 200


def wait_for_workspace(
    workspace_id: DaemonID,
    host: str = __default_host__,
    port: int = 8000,
) -> bool:
    url = _jinad_url(host, port, 'workspaces')
    while True:
        r = requests.get(f'{url}/{workspace_id}')
        try:
            state = r.json()['state']
        except KeyError as e:
            print(f'KeyError: {e!r}')
            return False
        if state in [
            RemoteWorkspaceState.PENDING,
            RemoteWorkspaceState.CREATING,
            RemoteWorkspaceState.UPDATING,
        ]:
            print(f'workspace still {state}, sleeping for 2 secs')
            time.sleep(2)
            continue
        elif state == RemoteWorkspaceState.ACTIVE:
            print(f'workspace got created successfully')
            return True
        elif state == RemoteWorkspaceState.FAILED:
            print(f'workspace creation failed. please check logs')
            return False


def create_flow(
    workspace_id: DaemonID,
    filename: str,
    host: str = __default_host__,
    port: int = 8000,
) -> str:
    url = _jinad_url(host, port, 'flows')
    r = requests.post(url, params={'workspace_id': workspace_id, 'filename': filename})
    print(f'Checking if the flow creation is succeeded: {r.json()}')
    assert r.status_code == 201
    return r.json()


def delete_flow(
    flow_id: DaemonID,
    host: str = __default_host__,
    port: int = 8000,
) -> bool:
    url = _jinad_url(host, port, f'flows/{flow_id}')
    r = requests.delete(url)
    return r.status_code == requests.codes.ok


def container_ip(container_name: str) -> str:
    import docker

    client = docker.from_env()
    container = client.containers.get(container_name)
    return container.attrs['NetworkSettings']['Networks']['jina_default']['IPAddress']
