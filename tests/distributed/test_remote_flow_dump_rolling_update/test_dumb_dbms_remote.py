import os
import shutil
from contextlib import ExitStack
from pathlib import Path
from typing import List

import numpy as np
import pytest
import requests

from jina import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))
dbms_flow_yml = os.path.join(cur_dir, 'flow_dbms.yml')
query_flow_yml = os.path.join(cur_dir, 'flow_query.yml')
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

JINAD_PORT_DBMS = '8001'
JINAD_PORT_QUERY = '8002'
REST_PORT_DBMS = '9000'
REST_PORT_QUERY = '9001'

DUMP_PATH_LOCAL = '/tmp/dump_path_mount/dump'
DUMP_PATH_DOCKER = '/tmp/dump_path_mount/dump'


SHARDS = 3

# TODO test
# 1 thread -- index
# -- query
# -- dump / rolling update


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote(tmpdir, docker_compose):
    nr_docs = 20
    nr_search = 1
    docs = list(_get_documents(nr=nr_docs, index_start=0, emb_size=10))

    # create dbms flow
    dbms_deps = [os.path.join(cur_dir, 'indexer_dbms.yml')]
    dbms_flow_id = _create_flow(
        dbms_flow_yml,
        dbms_deps,
        flow_url=f'http://localhost:{JINAD_PORT_DBMS}/flows',
        ws_url=f'http://localhost:{JINAD_PORT_DBMS}/workspaces',
    )

    query_deps = [os.path.join(cur_dir, 'indexer_query.yml')]
    query_flow_id = _create_flow(
        query_flow_yml,
        query_deps,
        flow_url=f'http://localhost:{JINAD_PORT_QUERY}/flows',
        ws_url=f'http://localhost:{JINAD_PORT_QUERY}/workspaces',
    )
    r = _send_rest_request(
        REST_PORT_QUERY,
        'search',
        'post',
        [doc.dict() for doc in docs[:nr_search]],
    )
    # TODO not sure
    assert (
        r['search']['docs'][0].get('matches') is None
        or r['search']['docs'][0].get('matches') is []
    )

    _send_rest_request(REST_PORT_DBMS, 'index', 'post', [doc.dict() for doc in docs])

    # jinad is used for ctrl requests
    _jinad_dump(
        'indexer_dbms',
        DUMP_PATH_DOCKER,  # the internal path in the docker container
        SHARDS,
        f'http://localhost:{JINAD_PORT_DBMS}/flows/{dbms_flow_id}',
    )

    dir_size = path_size(DUMP_PATH_LOCAL)
    assert dir_size > 0
    print(f'### dump path size: {dir_size} MBs')

    # jinad is used for ctrl requests
    _jinad_rolling_update(
        'indexer_query',
        DUMP_PATH_DOCKER,  # the internal path in the docker container
        f'http://localhost:{JINAD_PORT_QUERY}/flows/{query_flow_id}',
    )

    # data request goes to client
    r = _send_rest_request(
        REST_PORT_QUERY, 'search', 'post', [doc.dict() for doc in docs[:nr_search]]
    )
    assert len(r['search']['docs'][0].get('matches')) == nr_docs


def _create_flow(
    flow_yaml: str,
    deps: List[str],
    flow_url: str,
    ws_url: str,
) -> str:
    workspace_id = _create_workspace(deps, url=ws_url)
    with open(flow_yaml, 'rb') as f:
        r = requests.post(
            flow_url, data={'workspace_id': workspace_id}, files={'flow': f}
        )
        print(f'Checking if the flow creation has succeeded: {r.json()}')
        assert r.status_code == 201
        return r.json()


def _create_workspace(filepaths: List[str], url: str) -> str:
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


def path_size(dump_path):
    dir_size = (
        sum(f.stat().st_size for f in Path(dump_path).glob('**/*') if f.is_file()) / 1e6
    )
    return dir_size


def _send_rest_request(port_expose, endpoint, method, data):
    json = {'data': data}
    url = f'http://0.0.0.0:{port_expose}/{endpoint}'
    r = getattr(requests, method)(url, json=json)

    if r.status_code != 200:
        # TODO status_code should be 201 for index
        raise Exception(
            f'api request failed, url: {url}, status: {r.status_code}, content: {r.content} data: {data}'
        )
    return r.json()


def _get_documents(nr=10, index_start=0, emb_size=7):
    for i in range(index_start, nr + index_start):
        with Document() as d:
            d.id = i
            d.text = f'hello world {i}'
            d.embedding = np.random.random(emb_size)
            d.tags['tag_field'] = f'tag data {i}'
        yield d


def _jinad_dump(pod_name, dump_path, shards, url):
    params = {
        'kind': 'dump',
        'pod_name': pod_name,
        'dump_path': dump_path,
        'shards': shards,
    }
    # url params
    r = requests.put(url, params=params)
    assert r.status_code == 200


def _jinad_rolling_update(pod_name, dump_path, url):
    params = {
        'kind': 'rolling_update',
        'pod_name': pod_name,
        'dump_path': dump_path,
    }
    # url params
    r = requests.put(url, params=params)
    assert r.status_code == 200
