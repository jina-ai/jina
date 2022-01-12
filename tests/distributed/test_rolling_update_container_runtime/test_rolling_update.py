import os
import time

import numpy as np
import pytest
from daemon.models.id import DaemonID

from jina import Document, Client, __default_host__
from jina.logging.logger import JinaLogger
from daemon.clients import JinaDClient

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

HOST = __default_host__
JINAD_PORT = 8003
REST_PORT_DBMS = 9000
REST_PORT_QUERY = 9001
DUMP_PATH = '/jinad_workspace/dump'

logger = JinaLogger('test-dump')
client = JinaDClient(host=HOST, port=JINAD_PORT)

SHARDS = 3
EMB_SIZE = 10


@pytest.fixture
def executor_images():
    import docker

    client = docker.from_env()

    dbms_dir = os.path.join(cur_dir, 'pods', 'dbms')
    query_dir = os.path.join(cur_dir, 'pods', 'query')
    client.images.build(path=dbms_dir, tag='dbms-executor')
    client.images.build(path=query_dir, tag='query-executor')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()
    client.close()


def _create_flows():
    workspace_id = client.workspaces.create(paths=[cur_dir])
    dbms_flow_id = client.flows.create(
        workspace_id=workspace_id,
        filename='flow_dbms.yml',
        envs={'JINAD_WORKSPACE': f'/tmp/jinad/{workspace_id}'},
    )
    query_flow_id = client.flows.create(
        workspace_id=workspace_id,
        filename='flow_query.yml',
        envs={'JINAD_WORKSPACE': f'/tmp/jinad/{workspace_id}'},
    )
    return dbms_flow_id, query_flow_id, workspace_id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_dump_dbms_remote(executor_images, docker_compose):
    nr_docs = 100
    nr_search = 1
    docs = list(_get_documents(nr=nr_docs, index_start=0, emb_size=EMB_SIZE))

    dbms_flow_id, query_flow_id, workspace_id = _create_flows()

    # check that there are no matches in Query Flow
    r = Client(host=HOST, port=REST_PORT_QUERY, protocol='http').search(
        inputs=[doc for doc in docs[:nr_search]], return_results=True
    )
    assert r[0].data.docs[0].matches is None or len(r[0].data.docs[0].matches) == 0

    # index on DBMS flow
    Client(host=HOST, port=REST_PORT_DBMS, protocol='http').index(
        inputs=docs, return_results=True
    )

    # dump data for DBMS flow
    Client(host=HOST, port=REST_PORT_DBMS, protocol='http').post(
        on='/dump',
        parameters={'shards': SHARDS, 'dump_path': DUMP_PATH},
        target_executor='indexer_dbms',
    )

    # rolling_update on Query Flow
    assert (
        DaemonID(
            client.flows.rolling_update(
                id=query_flow_id,
                pod_name='indexer_query',
                uses_with={'dump_path': DUMP_PATH},
            )
        )
        == DaemonID(query_flow_id)
    )

    # validate that there are matches now
    r = Client(host=HOST, port=REST_PORT_QUERY, protocol='http').search(
        inputs=[doc for doc in docs[:nr_search]],
        return_results=True,
        parameters={'top_k': 10},
    )
    for doc in r[0].data.docs:
        assert len(doc.matches) == 10

    assert client.flows.delete(dbms_flow_id)
    assert client.flows.delete(query_flow_id)
    assert client.workspaces.delete(workspace_id)


def _get_documents(nr=10, index_start=0, emb_size=7):
    for i in range(index_start, nr + index_start):
        yield Document(
            id=str(i),
            text=f'hello world {i}',
            embedding=np.random.random(emb_size),
            tags={'tag_field': f'tag data {i}'},
        )
