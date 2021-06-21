import os
from ..helpers import create_flow

import numpy as np
import pytest
import requests

from jina import Document
from jina.logging.logger import JinaLogger

cur_dir = os.path.dirname(os.path.abspath(__file__))
dbms_flow_yml = os.path.join(cur_dir, 'flow_dbms.yml')
query_flow_yml = os.path.join(cur_dir, 'flow_query.yml')
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

JINAD_PORT_DBMS = '8001'
JINAD_PORT_QUERY = '8001'
REST_PORT_DBMS = '9000'
REST_PORT_QUERY = '9001'

DUMP_PATH_DOCKER = '/tmp/dump'

logger = JinaLogger('test-dump')

SHARDS = 3
EMB_SIZE = 10


def _path_size_remote(this_dump_path):
    os.system(
        f'docker exec jina_jinad_1 /bin/bash -c "du -sh {this_dump_path}" > dump_size.txt'
    )
    contents = open('dump_size.txt').readline()
    dir_size = float(contents.split('K')[0].split('M')[0])
    return dir_size


def _create_flows():
    # create dbms flow
    dbms_flow_id = create_flow(
        flow_yaml=dbms_flow_yml,
        pod_dir=os.path.join(cur_dir, 'pods'),
        url=f'http://localhost:{JINAD_PORT_DBMS}',
    )

    # create query flow
    query_flow_id = create_flow(
        flow_yaml=query_flow_yml,
        pod_dir=os.path.join(cur_dir, 'pods'),
        url=f'http://localhost:{JINAD_PORT_QUERY}',
    )
    return dbms_flow_id, query_flow_id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote(docker_compose):
    nr_docs = 100
    nr_search = 1
    docs = list(_get_documents(nr=nr_docs, index_start=0, emb_size=EMB_SIZE))

    dbms_flow_id, query_flow_id = _create_flows()

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

    # jinad is used for ctrl requests
    _jinad_dump(
        'indexer_dbms',
        DUMP_PATH_DOCKER,  # the internal path in the docker container
        SHARDS,
        f'http://localhost:{JINAD_PORT_DBMS}/flows/{dbms_flow_id}',
    )

    dir_size = _path_size_remote(DUMP_PATH_DOCKER)
    assert dir_size > 0
    logger.info(f'dump path size size: {dir_size}')

    # jinad is used for ctrl requests
    _jinad_rolling_update(
        'indexer_query',
        DUMP_PATH_DOCKER,  # the internal path in the docker container
        f'http://localhost:{JINAD_PORT_QUERY}/flows/{query_flow_id}',
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


def _send_rest_request(
    port_expose,
    endpoint,
    method,
    data,
    exec_endpoint=None,
    params=None,
    target_peapod=None,
    timeout=13,
):
    json = {'data': data}
    if params:
        json['parameters'] = params
    if target_peapod:
        json['target_peapod'] = target_peapod
    url = f'http://0.0.0.0:{port_expose}/{endpoint}'
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
