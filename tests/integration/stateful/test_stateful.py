import time

import pytest
import os

from jina import Client, Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port
from jina.serve.executors.decorators import write


class MyStateExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        for doc in docs:
            self.logger.debug(f'Indexing doc {doc.text}')
            self._docs.append(doc)

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        for doc in docs:
            doc.text = self._docs[doc.id].text
            doc.tags['pid'] = os.getpid()

    def snapshot(self, snapshot_file: str):
        self.logger.warning(
            f'Snapshotting to {snapshot_file} with {len(self._docs)} documents'
        )
        self.logger.warning(f'Snapshotting with order {[d.text for d in self._docs]}')
        with open(snapshot_file, 'wb') as f:
            self._docs.save_binary(f)

    def restore(self, snapshot_file: str):
        self._docs = DocumentArray.load_binary(snapshot_file)
        self.logger.warning(
            f'Restoring from {snapshot_file} with {len(self._docs)} documents'
        )
        self.logger.warning(f'Restoring with order {[d.text for d in self._docs]}')


class MyStateExecutorNoSnapshot(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        for doc in docs:
            self.logger.debug(f' Indexing doc {doc.text}')
            self._docs.append(doc)

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        for doc in docs:
            doc.text = self._docs[doc.id].text
            doc.tags['pid'] = os.getpid()


def assert_is_indexed(client, search_da):
    docs = client.search(inputs=search_da)
    for doc in docs:
        assert doc.text == f'ID {doc.id}'


def assert_all_replicas_indexed(client, search_da, num_replicas=3):
    for query in search_da:
        pids = set()
        for _ in range(10):
            for resp in client.search(inputs=query):
                pids.add(resp.tags['pid'])
                assert resp.text == f'ID {query.id}'
            if len(pids) == num_replicas:
                break
        assert len(pids) == num_replicas


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
def test_stateful_index_search(executor_cls, tmpdir):
    gateway_port = random_port()

    flow = Flow(port=gateway_port).add(
        uses=executor_cls,
        replicas=3,
        workspace=tmpdir,
        stateful=True,
        raft_configuration={
            'snapshot_interval': 10,
            'snapshot_threshold': 5,
            'trailing_logs': 10,
            'LogLevel': 'INFO',
        },
    )
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
        assert_all_replicas_indexed(flow, search_da)


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
def test_stateful_restore(executor_cls, tmpdir):
    gateway_port = random_port()

    flow = Flow(port=gateway_port).add(
        uses=executor_cls,
        replicas=3,
        workspace=tmpdir,
        stateful=True,
        raft_configuration={
            'snapshot_interval': 10,
            'snapshot_threshold': 5,
            'trailing_logs': 10,
            'LogLevel': 'INFO',
        },
    )
    with flow:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        flow.index(inputs=index_da)
        # allowing sometime for snapshots
        time.sleep(30)

    with flow:
        search_da = DocumentArray([Document(id=f'{i}') for i in range(100)])
        assert_all_replicas_indexed(flow, search_da)


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
def test_add_new_replica(executor_cls, tmpdir):
    from jina.parsers import set_pod_parser
    from jina.orchestrate.pods.factory import PodFactory
    gateway_port = random_port()

    flow = Flow(port=gateway_port).add(
        uses=executor_cls,
        replicas=3,
        workspace=tmpdir,
        stateful=True,
        raft_configuration={
            'snapshot_interval': 10,
            'snapshot_threshold': 5,
            'trailing_logs': 10,
            'LogLevel': 'INFO',
        },
    )
    with flow:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        flow.index(inputs=index_da)
        # allowing sometime for snapshots
        time.sleep(30)

        new_replica_port = random_port()
        args = set_pod_parser().parse_args([])
        args.host = args.host[0]
        args.port = [new_replica_port]
        args.stateful = True
        args.workspace = str(tmpdir)
        args.uses = executor_cls.__name__
        args.replica_id = '4'
        with PodFactory.build_pod(args) as p:
            import psutil
            current_pid = os.getpid()
            ports = set()
            for proc in psutil.process_iter(['pid', 'ppid', 'name']):
                if proc.info['ppid'] == current_pid and proc.info['pid'] != current_pid:
                    for conn in proc.connections():
                        if conn.status == 'LISTEN':
                            ports.add(conn.laddr.port)
            for port in ports:
                try:
                    leader_address = f'0.0.0.0:{port}'  # detect the Pods addresses of the original Flow
                    voter_address = f'0.0.0.0:{new_replica_port}'
                    import jraft
                    jraft.add_voter(
                        leader_address, '4', voter_address
                    )
                    break
                except:
                    pass
            time.sleep(10)
            search_da = DocumentArray([Document(id=f'{i}') for i in range(100)])
            client = Client(port=new_replica_port)
            assert_is_indexed(client, search_da=search_da)
