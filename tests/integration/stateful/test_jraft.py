import multiprocessing
import os
import time

import pytest

from jina import Client, Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port
from jina.serve.executors.decorators import write
from jina.serve.helper import _get_workspace_from_name_and_shards

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


class MyStateExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        time.sleep(0.2)
        for doc in docs:
            self.logger.debug(f' Indexing doc {doc.text}')
            self._docs.append(doc)

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        time.sleep(0.2)
        for doc in docs:
            doc.text = self._docs[doc.id].text

    def snapshot(self, snapshot_file: str):
        self.logger.warning(
            f' Snapshotting to {snapshot_file} with {len(self._docs)} documents'
        )
        self.logger.warning(f'Snapshotting with order {[d.text for d in self._docs]}')
        with open(snapshot_file, 'wb') as f:
            self._docs.save_binary(f)

    def restore(self, snapshot_file: str):
        self._docs = DocumentArray.load_binary(snapshot_file)
        self.logger.warning(
            f' Restoring from {snapshot_file} with {len(self._docs)} documents'
        )
        self.logger.warning(f'Restoring with order {[d.text for d in self._docs]}')


def assert_is_indexed(client, search_da):
    docs = client.search(inputs=search_da)
    for doc in docs:
        assert doc.text == f'ID {doc.id}'


def run_flow_index_and_assert(flow, pod_ports):
    with flow:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        search_da = DocumentArray([Document(id=f'{i}') for i in range(100)])
        flow.index(inputs=index_da)

        # allowing some time for the state to be replicated
        time.sleep(20)
        # checking against the main read replica
        assert_is_indexed(flow, search_da)


def test_get_configuration(tmpdir):
    gateway_port = random_port()
    pod_ports = [random_port(), random_port(), random_port()]

    print('###################################', pod_ports)
    flow = Flow(port=gateway_port).add(
        uses=MyStateExecutor,
        replicas=3,
        workspace=tmpdir,
        pod_ports=pod_ports,
        stateful=True,
        raft_configuration={
            'snapshot_interval': 10,
            'snapshot_threshold': 5,
            'trailing_logs': 10,
            'LogLevel': 'INFO',
        },
    )

    process = multiprocessing.Process(
        target=run_flow_index_and_assert, args=(flow, pod_ports)
    )
    process.start()
    process.join()
    assert process.exitcode == 0

    import jraft

    for raft_id in range(3):
        raft_dir = _get_workspace_from_name_and_shards(
            workspace=tmpdir, name='raft', shard_id=-1
        )
        persisted_address = jraft.get_configuration(str(raft_id), raft_dir)
        print('###################################', raft_dir)
        assert persisted_address == f'0.0.0.0:{pod_ports[raft_id]}'
