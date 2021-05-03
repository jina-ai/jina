import shutil
import os
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from threading import Thread
from typing import List

import numpy as np
import pytest
import requests

from jina import Document, Client
from jina.logging import JinaLogger

cur_dir = os.path.dirname(os.path.abspath(__file__))
dbms_flow_yml = os.path.join(cur_dir, 'flow_dbms.yml')
query_flow_yml = os.path.join(cur_dir, 'flow_query.yml')
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

JINAD_PORT_DBMS = '8000'
JINAD_PORT_QUERY = '8000'
REST_PORT_DBMS = '9000'
REST_PORT_QUERY = '9001'

DUMP_PATH_LOCAL = '/tmp/dump_path_mount/dump'
DUMP_PATH_DOCKER = '/tmp/dump_path_mount/dump'

logger = JinaLogger('test-dump')

SHARDS = 3
EMB_SIZE = 10

# global between threads
KEEP_RUNNING = True
INDEX_TIMES = 0
QUERY_TIMES = 0
DUMP_ROLL_UPDATE_TIME = 0


class MyThread(Thread):
    def run(self) -> None:
        try:
            super().run()
        except Exception as e:
            logger.error(sys.exc_info())
            raise e


def _index_client(nr_docs_index):
    global INDEX_TIMES
    logger.info(f'starting index thread. KEEP_RUNNING = {KEEP_RUNNING}')
    while KEEP_RUNNING:
        docs = list(
            _get_documents(
                nr=nr_docs_index,
                index_start=INDEX_TIMES * nr_docs_index,
                emb_size=EMB_SIZE,
            )
        )
        Client.check_input(docs)
        logger.info(f'indexing {len(docs)} docs...')
        _send_rest_request(
            REST_PORT_DBMS, 'index', 'post', [doc.dict() for doc in docs]
        )
        INDEX_TIMES += 1
        time.sleep(4)


def _query_client(nr_docs_query):
    global QUERY_TIMES
    logger.info(f'starting query thread. KEEP_RUNNING = {KEEP_RUNNING}')
    prev_len_matches = 0
    docs = list(_get_documents(nr=nr_docs_query, index_start=0, emb_size=EMB_SIZE))
    Client.check_input(docs)
    while KEEP_RUNNING:
        try:
            logger.info(f'querying...')
            r = _send_rest_request(
                REST_PORT_QUERY,
                'search',
                'post',
                [doc.dict() for doc in docs],
                timeout=5,
            )
            for doc in r['search']['docs']:
                len_matches = len(doc.get('matches'))
                assert len_matches >= prev_len_matches
            logger.info(f'got {len_matches} matches')
            prev_len_matches = len_matches
            QUERY_TIMES += 1
            time.sleep(2)
        except Exception as e:
            logger.error(f'querying failed: {e}. trying again...')


def _dump_roll_update(dbms_flow_id, query_flow_id):
    global DUMP_ROLL_UPDATE_TIME
    logger.info(f'starting _dump_roll_update thread. KEEP_RUNNING = {KEEP_RUNNING}')
    folder_id = 10
    while KEEP_RUNNING:
        this_dump_path = os.path.join(DUMP_PATH_DOCKER, f'dump-{folder_id}')
        # jinad is used for ctrl requests
        logger.info(f'dumping...')
        _jinad_dump(
            'indexer_dbms',
            this_dump_path,  # the internal path in the docker container
            SHARDS,
            f'http://localhost:{JINAD_PORT_DBMS}/flows/{dbms_flow_id}',
        )

        logger.info(f'checking size...')
        dir_size = path_size(DUMP_PATH_LOCAL)
        assert dir_size > 0
        logger.info(f'dump path size: {dir_size} MBs')

        # jinad is used for ctrl requests
        logger.info(f'rolling update...')
        _jinad_rolling_update(
            'indexer_query',
            this_dump_path,  # the internal path in the docker container
            f'http://localhost:{JINAD_PORT_QUERY}/flows/{query_flow_id}',
        )
        folder_id += 1
        logger.info(f'rolling update done!')
        DUMP_ROLL_UPDATE_TIME += 1
        time.sleep(4)


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote_stress(tmpdir, docker_compose):
    global KEEP_RUNNING
    nr_docs_index = 5
    nr_docs_search = 1

    time.sleep(2)
    dbms_flow_id, query_flow_id = _create_flows()
    time.sleep(4)

    query_thread = MyThread(
        target=_query_client, name='_query_client', args=(nr_docs_search,), daemon=True
    )
    query_thread.start()

    index_thread = MyThread(
        target=_index_client, name='_index_client', args=(nr_docs_index,), daemon=True
    )
    index_thread.start()

    # give it time to index
    time.sleep(2)
    dump_roll_update_thread = MyThread(
        target=_dump_roll_update,
        name='_dump_roll_update',
        args=(dbms_flow_id, query_flow_id),
        daemon=True,
    )
    dump_roll_update_thread.start()

    threads = [query_thread, index_thread, dump_roll_update_thread]

    logger.info('sleeping')
    time.sleep(30)

    for t in threads:
        if not t.is_alive():
            logger.warning(f'something went wrong in thread {t.name}')
            t.join()
            assert False, f'check error from thread {t.name}'

    assert INDEX_TIMES > 3
    assert QUERY_TIMES > 3
    assert DUMP_ROLL_UPDATE_TIME > 3

    logger.info(f'ending and exit threads')


def _create_flows():
    # create dbms flow
    dbms_deps = [os.path.join(cur_dir, 'indexer_dbms.yml')]
    dbms_flow_id = _create_flow(
        dbms_flow_yml,
        dbms_deps,
        flow_url=f'http://localhost:{JINAD_PORT_DBMS}/flows',
        ws_url=f'http://localhost:{JINAD_PORT_DBMS}/workspaces',
    )
    # create query flow
    query_deps = [os.path.join(cur_dir, 'indexer_query.yml')]
    query_flow_id = _create_flow(
        query_flow_yml,
        query_deps,
        flow_url=f'http://localhost:{JINAD_PORT_QUERY}/flows',
        ws_url=f'http://localhost:{JINAD_PORT_QUERY}/workspaces',
    )
    return dbms_flow_id, query_flow_id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote(tmpdir, docker_compose):
    nr_docs = 20
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
        r['search']['docs'][0].get('matches') is None
        or r['search']['docs'][0].get('matches') == []
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
    logger.info(f'dump path size: {dir_size} MBs')

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
    for doc in r['search']['docs']:
        assert len(doc.get('matches')) == nr_docs


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
        logger.info(f'Checking if the flow creation has succeeded: {r.json()}')
        assert r.status_code == 201
        return r.json()


def _create_workspace(filepaths: List[str], url: str) -> str:
    with ExitStack() as file_stack:
        files = [
            ('files', file_stack.enter_context(open(filepath, 'rb')))
            for filepath in filepaths
        ]
        logger.info(f'uploading {files}')
        r = requests.post(url, files=files)
        assert r.status_code == 201

        workspace_id = r.json()
        logger.info(f'Got workspace_id: {workspace_id}')
        return workspace_id


def path_size(dump_path):
    dir_size = (
        sum(f.stat().st_size for f in Path(dump_path).glob('**/*') if f.is_file()) / 1e6
    )
    return dir_size


def _send_rest_request(port_expose, endpoint, method, data, timeout=13):
    json = {'data': data}
    url = f'http://0.0.0.0:{port_expose}/{endpoint}'
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
        'kind': 'dump',
        'pod_name': pod_name,
        'dump_path': dump_path,
        'shards': shards,
    }
    # url params
    logger.info(f'sending PUT req to dump')
    r = requests.put(url, params=params)
    assert r.status_code == 200


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


@pytest.fixture()
def cleanup_dump():
    shutil.rmtree(DUMP_PATH_LOCAL, ignore_errors=True)
    yield
    shutil.rmtree(DUMP_PATH_LOCAL)
