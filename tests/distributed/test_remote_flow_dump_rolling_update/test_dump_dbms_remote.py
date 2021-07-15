import os

import numpy as np
import pytest
import requests

from jina import Document
from jina.logging.logger import JinaLogger
from ..helpers import (
    create_flow,
    create_workspace,
    wait_for_workspace,
    delete_workspace,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))
dbms_flow_yml = os.path.join(cur_dir, 'flow_dbms.yml')
query_flow_yml = os.path.join(cur_dir, 'flow_query.yml')
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

JINAD_PORT = '8000'
JINAD_PORT_DBMS = '8001'
JINAD_PORT_QUERY = '8001'
REST_PORT_DBMS = '9000'
REST_PORT_QUERY = '9001'

DUMP_PATH_DOCKER = '/workspace/dump'

logger = JinaLogger('test-dump')

SHARDS = 3
EMB_SIZE = 10


def _path_size_remote(this_dump_path, container_id):
    os.system(
        f'docker exec {container_id} /bin/bash -c "du -sh {this_dump_path}" > dump_size.txt'
    )
    contents = open('dump_size.txt').readline()
    dir_size = float(contents.split('K')[0].split('M')[0])
    return dir_size


def _create_flows(ip):
    workspace_id = create_workspace(
        filepaths=[dbms_flow_yml, query_flow_yml],
        host=ip,
        dirpath=os.path.join(cur_dir, 'pods'),
    )
    assert wait_for_workspace(workspace_id, host=ip)
    # create dbms flow
    dbms_flow_id = create_flow(
        workspace_id=workspace_id, filename='flow_dbms.yml', host=ip
    )

    # create query flow
    query_flow_id = create_flow(
        workspace_id=workspace_id, filename='flow_query.yml', host=ip
    )
    return dbms_flow_id, query_flow_id, workspace_id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote(docker_compose):
    nr_docs = 100
    nr_search = 1
    docs = list(_get_documents(nr=nr_docs, index_start=0, emb_size=EMB_SIZE))
    jinad_ip = 'localhost'

    dbms_flow_id, query_flow_id, workspace_id = _create_flows(jinad_ip)

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

    container_id = get_container_id(dbms_flow_id, jinad_ip)
    dir_size = _path_size_remote(DUMP_PATH_DOCKER, container_id=container_id)
    assert dir_size > 0
    logger.info(f'dump path size size: {dir_size}')

    # jinad is used for ctrl requests
    _jinad_rolling_update(
        'indexer_query',
        DUMP_PATH_DOCKER,  # the internal path in the docker container
        f'http://{jinad_ip}:{JINAD_PORT}/flows/{query_flow_id}',
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

    delete_workspace(workspace_id=workspace_id, host=jinad_ip)


def get_container_id(flow_id, jinad_ip):
    response = requests.get(f'http://{jinad_ip}:{JINAD_PORT}/flows/{flow_id}')
    container_id = response.json()['metadata']['container_id']
    return container_id


def _send_rest_request(
    port_expose,
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
    url = f'http://{ip}:{port_expose}/{endpoint}'
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
        with Document() as d:
            d.id = i
            d.text = f'hello world {i}'
            d.embedding = np.random.random(emb_size)
            d.tags['tag_field'] = f'tag data {i}'
        yield d


def _jinad_dump(pod_name, dump_path, shards, url):
    params = {
        'pod_name': pod_name,
        'dump_path': dump_path,
        'shards': shards,
    }
    # url params
    logger.info(f'sending dump request')
    _send_rest_request(
        REST_PORT_DBMS,
        'post',
        'post',
        data=[],
        exec_endpoint='/dump',
        params=params,
        target_peapod=pod_name,
    )


def _jinad_rolling_update(pod_name, dump_path, url):
    params = {
        'kind': 'rolling_update',
        'pod_name': pod_name,
        'dump_path': dump_path,
    }
    # url params
    logger.info(f'sending PUT to roll update')
    r = requests.put(url, params=params)
    assert r.status_code == 200
