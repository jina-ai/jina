import os
import sys
import time
import traceback
from contextlib import ExitStack
from pathlib import Path
from threading import Thread
from typing import List

import numpy as np
import pytest
import requests
from requests.exceptions import ConnectionError
from urllib3.exceptions import ReadTimeoutError, NewConnectionError

from jina import Document, Client
from jina.logging import JinaLogger

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
        time.sleep(7)


def _query_client(nr_docs_query):
    global QUERY_TIMES
    logger.info(f'starting query thread. KEEP_RUNNING = {KEEP_RUNNING}')
    prev_len_matches = 0
    docs = list(_get_documents(nr=nr_docs_query, index_start=0, emb_size=EMB_SIZE))
    Client.check_input(docs)
    query_docs = [doc.dict() for doc in docs]
    while KEEP_RUNNING:
        try:
            logger.info(f'querying...')
            r = _send_rest_request(
                REST_PORT_QUERY,
                'search',
                'post',
                query_docs,
                timeout=8,
            )
            for doc in r['search']['docs']:
                len_matches = len(doc.get('matches'))
                assert len_matches >= prev_len_matches
            logger.info(f'got {len_matches} matches')
            if len_matches != prev_len_matches:
                # only count queries after a change in index size
                QUERY_TIMES += 1
            prev_len_matches = len_matches
            time.sleep(3)
        except (ConnectionError, ReadTimeoutError) as e:
            logger.error(f'querying failed: {e}. trying again...')
            logger.error(traceback.format_exc())
        except (NewConnectionError, Exception) as e:
            logger.error(f'error in query thread: {e!r}')
            raise e


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
        dir_size = _path_size_remote(this_dump_path)
        assert dir_size > 0
        logger.info(f'dump path size: {dir_size}')

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
        time.sleep(10)


def _path_size_remote(this_dump_path):
    os.system(
        f'docker exec jina_jinad_1 /bin/bash -c "du -sh {this_dump_path}" > dump_size.txt'
    )
    contents = open('dump_size.txt').readline()
    dir_size = float(contents.split('K')[0].split('M')[0])
    return dir_size


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote_stress(docker_compose):
    global KEEP_RUNNING
    nr_docs_index = 20
    nr_docs_search = 3

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
    time.sleep(60)
    KEEP_RUNNING = False

    for t in threads:
        if not t.is_alive():
            logger.warning(f'something went wrong in thread {t.name}')
            t.join()
            assert False, f'check error from thread {t.name}'

    assert INDEX_TIMES > 3
    assert QUERY_TIMES > 3
    assert DUMP_ROLL_UPDATE_TIME > 2

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
