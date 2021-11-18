import os

import numpy as np
import pytest
import requests
from daemon.models.id import DaemonID

from jina import Document
from jina.logging.logger import JinaLogger
from daemon.clients import JinaDClient

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

JINAD_PORT = '8000'
JINAD_PORT_DBMS = '8001'
JINAD_PORT_QUERY = '8001'
REST_PORT_DBMS = '9000'
REST_PORT_QUERY = '9001'

DUMP_PATH_DOCKER = '/workspace/dump'

logger = JinaLogger('test-dump')
client = JinaDClient(host='localhost', port=JINAD_PORT)

SHARDS = 3
EMB_SIZE = 10


def _path_size_remote(this_dump_path, container_id):
    os.system(
        f'docker exec {container_id} /bin/bash -c "du -sh {this_dump_path}" > dump_size.txt'
    )
    contents = open('dump_size.txt').readline()
    dir_size = float(contents.split('K')[0].split('M')[0])
    return dir_size


def _create_flows():
    workspace_id = client.workspaces.create(paths=[cur_dir])
    dbms_flow_id = client.flows.create(
        workspace_id=workspace_id, filename='flow_dbms.yml'
    )
    query_flow_id = client.flows.create(
        workspace_id=workspace_id, filename='flow_query.yml'
    )
    return dbms_flow_id, query_flow_id, workspace_id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote(docker_compose):
    nr_docs = 100
    nr_search = 1
    docs = list(_get_documents(nr=nr_docs, index_start=0, emb_size=EMB_SIZE))

    dbms_flow_id, query_flow_id, workspace_id = _create_flows()

    r = _send_rest_request(
        REST_PORT_QUERY,
        'search',
        'post',
        [doc.dict() for doc in docs[:nr_search]],
    )
    # TODO some times it was None
    assert (
        r['data']['docs'][0].get('matches') is None
        or r['data']['docs'][0].get('matches') == []
    )

    _send_rest_request(REST_PORT_DBMS, 'index', 'post', [doc.dict() for doc in docs])

    _send_rest_request(
        REST_PORT_DBMS,
        'post',
        'post',
        data=[],
        exec_endpoint='/dump',
        params={'shards': SHARDS, 'dump_path': DUMP_PATH_DOCKER},
        target_peapod='indexer_dbms',
    )

    container_id = client.flows.get(dbms_flow_id)['metadata']['container_id']
    dir_size = _path_size_remote(DUMP_PATH_DOCKER, container_id=container_id)
    assert dir_size > 0
    logger.info(f'dump path size size: {dir_size}')

    # jinad is used for ctrl requests
    assert (
        DaemonID(
            client.flows.rolling_update(
                id=query_flow_id,
                pod_name='indexer_query',
                uses_with={'dump_path': DUMP_PATH_DOCKER},
            )
        )
        == DaemonID(query_flow_id)
    )

    # data request goes to client
    r = _send_rest_request(
        REST_PORT_QUERY,
        'search',
        'post',
        [doc.dict() for doc in docs[:nr_search]],
        params={'top_k': 100},
    )
    for doc in r['data']['docs']:
        assert len(doc.get('matches')) == nr_docs

    assert client.flows.delete(dbms_flow_id)
    assert client.flows.delete(query_flow_id)
    assert client.workspaces.delete(workspace_id)


def _send_rest_request(
    port,
    endpoint,
    method,
    data,
    exec_endpoint=None,
    params=None,
    target_peapod=None,
    timeout=13,
    ip='0.0.0.0',
):
    json = {'data': data}
    if params:
        json['parameters'] = params
    if target_peapod:
        json['target_peapod'] = target_peapod
    url = f'http://{ip}:{port}/{endpoint}'
    if endpoint == 'post':
        json['exec_endpoint'] = exec_endpoint
    logger.info(f'sending {method} request to {url}')
    r = getattr(requests, method)(url, json=json, timeout=timeout)

    if r.status_code != 200:
        # TODO status_code should be 201 for index
        raise Exception(
            f'api request failed, url: {url}, status: {r.status_code}, content: {r.content} data: {data}'
        )
    return r.json()


def _get_documents(nr=10, index_start=0, emb_size=7):
    for i in range(index_start, nr + index_start):
        yield Document(
            id=i,
            text=f'hello world {i}',
            embedding=np.random.random(emb_size),
            tags={'tag_field': f'tag data {i}'},
        )
