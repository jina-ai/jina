import multiprocessing
import os
import time

import pytest

from jina import Client, Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port
from jina.orchestrate.pods.factory import PodFactory
from jina.parsers import set_pod_parser
from jina.serve.executors.decorators import write

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


class MyStateExecutorNoSnapshot(Executor):
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
        time.sleep(10)
        # checking against the main read replica
        assert_is_indexed(flow, search_da)

        # performing manual requests to the underlying replicas
        executor_ports = [(port + 1) for port in pod_ports]
        for port in executor_ports:
            client = Client(port=port)
            assert_is_indexed(client, search_da)


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
def test_stateful_index_search(executor_cls, tmpdir):
    gateway_port = random_port()
    pod_ports = [random_port(), random_port(), random_port()]

    flow = Flow(port=gateway_port).add(
        uses=executor_cls,
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


def run_flow_index(flow):
    with flow:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        flow.index(inputs=index_da)
        # allowing sometime for snapshots
        time.sleep(30)


def restore_flow_search(flow):
    with flow:
        search_da = DocumentArray([Document(id=f'{i}') for i in range(100)])
        assert_is_indexed(flow, search_da)


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
def test_stateful_restore(executor_cls, tmpdir):
    gateway_port = random_port()
    pod_ports = [random_port(), random_port(), random_port()]

    flow = Flow(port=gateway_port).add(
        uses=executor_cls,
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

    process = multiprocessing.Process(target=run_flow_index, args=(flow,))
    process.start()
    process.join()
    assert process.exitcode == 0

    process = multiprocessing.Process(target=restore_flow_search, args=(flow,))
    process.start()
    process.join()
    assert process.exitcode == 0
