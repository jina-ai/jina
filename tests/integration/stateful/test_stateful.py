import time

import pytest
import os

from jina import Client, Document, DocumentArray, Executor, Flow, requests, Deployment
from jina.helper import random_port
from jina.serve.executors.decorators import write

from tests.integration.stateful.stateful_no_snapshot_exec.executor import MyStateExecutorNoSnapshot
from tests.integration.stateful.stateful_snapshot_exec.executor import MyStateExecutor


cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def stateful_exec_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'stateful_snapshot_exec/'), tag='stateful-exec'
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()

@pytest.fixture(scope='module')
def stateful_no_snapshot_exec_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'stateful_no_snapshot_exec/'), tag='stateful-no-snapshot-exec'
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def assert_is_indexed(client, search_da):
    docs = client.search(inputs=search_da, request_size=1)
    for doc in docs:
        assert doc.text == f'ID {doc.id}'


def assert_all_replicas_indexed(client, search_da, num_replicas=3):
    for query in search_da:
        pids = set()
        for _ in range(10):
            for resp in client.search(inputs=query, request_size=1):
                pids.add(resp.tags['pid'])
                assert resp.text == f'ID {query.id}'
            if len(pids) == num_replicas:
                break
        assert len(pids) == num_replicas


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot, 'docker://stateful-exec', 'docker://stateful-no-snapshot-exec'])
@pytest.mark.parametrize('ctx', ['deployment', 'flow'])
@pytest.mark.parametrize('shards', [1, 2])
def test_stateful_index_search(executor_cls, ctx, shards, tmpdir, stateful_exec_docker_image_built, stateful_no_snapshot_exec_docker_image_built):
    replicas = 3
    peer_ports = {}
    for shard in range(shards):
        peer_ports[shard] = [random_port() for _ in range(replicas)]
    if ctx == 'flow':
        gateway_port = random_port()
        ctx_mngr = Flow(port=gateway_port).add(
            uses=executor_cls,
            replicas=replicas,
            workspace=tmpdir,
            stateful=True,
            raft_configuration={
                'snapshot_interval': 10,
                'snapshot_threshold': 5,
                'trailing_logs': 10,
                'LogLevel': 'INFO',
            },
            shards=shards,
            peer_ports=peer_ports,
            polling={'/index': 'ANY', '/search': 'ALL'}
        )
    elif ctx == 'deployment':
        ctx_mngr = Deployment(
            uses=executor_cls,
            replicas=replicas,
            workspace=tmpdir,
            stateful=True,
            raft_configuration={
                'snapshot_interval': 10,
                'snapshot_threshold': 5,
                'trailing_logs': 10,
                'LogLevel': 'INFO',
            },
            shards=shards,
            peer_ports=peer_ports,
            polling={'/index': 'ANY', '/search': 'ALL'}
        )
    with ctx_mngr:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        search_da = DocumentArray([Document(id=f'{i}') for i in range(100)])
        ctx_mngr.index(inputs=index_da, request_size=1)

        # allowing some time for the state to be replicated
        time.sleep(10)
        # checking against the main read replica
        assert_is_indexed(ctx_mngr, search_da)
        assert_all_replicas_indexed(ctx_mngr, search_da)


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
@pytest.mark.parametrize('ctx', ['flow', 'deployment'])
@pytest.mark.parametrize('shards', [1, 2])
def test_stateful_restore(executor_cls, ctx, shards, tmpdir):
    replicas = 3
    peer_ports = {}
    for shard in range(shards):
        peer_ports[shard] = [random_port() for _ in range(replicas)]
    if ctx == 'flow':
        gateway_port = random_port()

        ctx_mngr = Flow(port=gateway_port).add(
            uses=executor_cls,
            replicas=replicas,
            workspace=tmpdir,
            stateful=True,
            raft_configuration={
                'snapshot_interval': 10,
                'snapshot_threshold': 5,
                'trailing_logs': 10,
                'LogLevel': 'INFO',
            },
            peer_ports=peer_ports,
            shards=shards,
            polling={'/index': 'ANY', '/search': 'ALL'}
        )
    elif ctx == 'deployment':
        ctx_mngr = Deployment(uses=executor_cls,
                              replicas=replicas,
                              workspace=tmpdir,
                              stateful=True,
                              raft_configuration={
                                  'snapshot_interval': 10,
                                  'snapshot_threshold': 5,
                                  'trailing_logs': 10,
                                  'LogLevel': 'INFO',
                              },
                              shards=shards,
                              peer_ports=peer_ports,
                              polling={'/index': 'ANY', '/search': 'ALL'})
    with ctx_mngr:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        ctx_mngr.index(inputs=index_da, request_size=1)
        # allowing sometime for snapshots
        time.sleep(30)

    with ctx_mngr:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100, 200)]
        )
        ctx_mngr.index(inputs=index_da, request_size=1)
        time.sleep(5)
        search_da = DocumentArray([Document(id=f'{i}') for i in range(200)])
        assert_all_replicas_indexed(ctx_mngr, search_da)


@pytest.mark.parametrize('executor_cls', [MyStateExecutor])
@pytest.mark.parametrize('ctx', ['flow'])
def test_add_new_replica(executor_cls, ctx, tmpdir):
    from jina.parsers import set_pod_parser
    from jina.orchestrate.pods.factory import PodFactory
    if ctx == 'flow':
        gateway_port = random_port()

        ctx_mngr = Flow(port=gateway_port).add(
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
    elif ctx == 'deployment':
        ctx_mngr = Deployment(uses=executor_cls,
                              replicas=3,
                              workspace=tmpdir,
                              stateful=True,
                              raft_configuration={
                                  'snapshot_interval': 10,
                                  'snapshot_threshold': 5,
                                  'trailing_logs': 10,
                                  'LogLevel': 'INFO',
                              })
    with ctx_mngr:
        index_da = DocumentArray(
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        ctx_mngr.index(inputs=index_da, request_size=1)
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
            index_da = DocumentArray(
                [Document(id=f'{i}', text=f'ID {i}') for i in range(100, 200)]
            )
            ctx_mngr.index(inputs=index_da, request_size=1)
            time.sleep(10)
            search_da = DocumentArray([Document(id=f'{i}') for i in range(200)])
            client = Client(port=new_replica_port)
            assert_is_indexed(client, search_da=search_da)
