import time

import pytest
import os

from jina import Client, Document, DocumentArray, Flow, Deployment
from typing import Dict, List

from jina.helper import random_port

from tests.integration.stateful.stateful_no_snapshot_exec.executor import MyStateExecutorNoSnapshot
from tests.integration.stateful.stateful_snapshot_exec.executor import MyStateExecutor
from jina._docarray import docarray_v2

if docarray_v2:
    from docarray.documents import TextDoc

cur_dir = os.path.dirname(os.path.abspath(__file__))


class TextDocWithId(TextDoc):
    id: str
    tags: Dict[str, str] = {}
    l: List[str] = []


@pytest.fixture(scope='function')
def kill_all_children():
    yield
    from multiprocessing import active_children
    children = active_children()
    for p in children:
        print(f' Child process {p.pid} is still active')
        p.kill()


@pytest.fixture(scope='module')
def stateful_exec_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'stateful_snapshot_exec/'), tag='stateful-exec'
    )
    client.close()
    yield
    time.sleep(3)
    client = docker.from_env()
    client.containers.prune()


def assert_is_indexed(client, search_da):
    docs = client.search(inputs=search_da, request_size=1, return_type=DocumentArray[TextDocWithId])
    for doc in docs:
        assert doc.text == f'ID {doc.id}'


def assert_all_replicas_indexed(client, search_da, num_replicas=3, key='pid'):
    for query in search_da:
        pids = set()
        for _ in range(10):
            for resp in client.search(inputs=query, request_size=1, return_type=DocumentArray[TextDocWithId]):
                pids.add(resp.tags[key])
                assert resp.text == f'ID {query.id}'
            if len(pids) == num_replicas:
                break
        assert len(pids) == num_replicas


@pytest.mark.timeout(240)
@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
@pytest.mark.parametrize('shards', [2, 1])
@pytest.mark.skipif(not docarray_v2, reason='tests support for docarray>=0.30')
def test_stateful_index_search(executor_cls, shards, tmpdir, stateful_exec_docker_image_built, kill_all_children):
    replicas = 3
    if shards > 1:
        peer_ports = {}
        for shard in range(shards):
            peer_ports[shard] = [random_port() for _ in range(replicas)]
    else:
        peer_ports = [random_port() for _ in range(replicas)]
    dep = Deployment(
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
        volumes=[str(tmpdir) + ':' + '/workspace'],
        peer_ports=peer_ports,
        polling={'/index': 'ANY', '/search': 'ALL', '/similarity': 'ALL'}
    )
    with dep:
        index_da = DocumentArray[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        search_da = DocumentArray[TextDocWithId]([TextDocWithId(id=f'{i}') for i in range(1)])
        dep.index(inputs=index_da, request_size=1, return_type=DocumentArray[TextDocWithId])

        # allowing some time for the state to be replicated
        time.sleep(20)
        # checking against the main read replica
        assert_is_indexed(dep, search_da)
        assert_all_replicas_indexed(dep, search_da)
        docs = dep.post(on='/similarity', inputs=search_da, request_size=1,
                        return_type=DocumentArray[TextDocWithId])
        for doc in docs:
            assert doc.text == 'similarity'
            assert len(doc.l) == len(index_da)  # good merging of results


@pytest.mark.timeout(240)
@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
@pytest.mark.parametrize('shards', [2, 1])
@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ or not docarray_v2, reason='tests support for docarray>=0.30 and not working on GITHUB since issue with restarting server in grpc')
def test_stateful_index_search_restore(executor_cls, shards, tmpdir, stateful_exec_docker_image_built,
                                       kill_all_children):
    replicas = 3
    peer_ports = {}
    for shard in range(shards):
        peer_ports[shard] = [random_port() for _ in range(replicas)]
    dep = Deployment(
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
        volumes=[str(tmpdir) + ':' + '/workspace'],
        peer_ports=peer_ports,
        polling={'/index': 'ANY', '/search': 'ALL', '/similarity': 'ALL'}
    )
    with dep:
        index_da = DocumentArray[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        search_da = DocumentArray[TextDocWithId]([TextDocWithId(id=f'{i}') for i in range(1)])
        dep.index(inputs=index_da, request_size=1, return_type=DocumentArray[TextDocWithId])

        # allowing some time for the state to be replicated
        time.sleep(20)
        # checking against the main read replica
        assert_is_indexed(dep, search_da)
        assert_all_replicas_indexed(dep, search_da)

    # test restoring
    with dep:
        index_da = DocumentArray[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100, 200)]
        )
        dep.index(inputs=index_da, request_size=1, return_type=DocumentArray[TextDocWithId])
        time.sleep(20)
        search_da = DocumentArray[TextDocWithId]([TextDocWithId(id=f'{i}') for i in range(200)])
        assert_all_replicas_indexed(dep, search_da)


@pytest.mark.skip('Not sure how containerization will work with docarray v2')
@pytest.mark.parametrize('shards', [1, 2])
def test_stateful_index_search_container(shards, tmpdir, stateful_exec_docker_image_built):
    replicas = 3
    peer_ports = {}
    for shard in range(shards):
        peer_ports[shard] = [random_port() for _ in range(replicas)]

    dep = Deployment(
        uses='docker://stateful-exec',
        replicas=replicas,
        stateful=True,
        raft_configuration={
            'snapshot_interval': 10,
            'snapshot_threshold': 5,
            'trailing_logs': 10,
            'LogLevel': 'INFO',
        },
        shards=shards,
        workspace='/workspace/tmp',
        volumes=[str(tmpdir) + ':' + '/workspace/tmp'],
        peer_ports=peer_ports,
        polling={'/index': 'ANY', '/search': 'ALL', '/similarity': 'ALL'}
    )
    with dep:
        index_da = DocumentArray[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100)]
        )
        search_da = DocumentArray[TextDocWithId]([TextDocWithId(id=f'{i}') for i in range(100)])
        dep.index(inputs=index_da, request_size=1, return_type=DocumentArray[TextDocWithId])

        # allowing some time for the state to be replicated
        time.sleep(10)
        # checking against the main read replica
        assert_is_indexed(dep, search_da)
        assert_all_replicas_indexed(dep, search_da, key='random_num')

    # test restoring
    with dep:
        index_da = DocumentArray[TextDocWithId](
            [Document(id=f'{i}', text=f'ID {i}') for i in range(100, 200)]
        )
        dep.index(inputs=index_da, request_size=1, return_type=DocumentArray[TextDocWithId])
        time.sleep(10)
        search_da = DocumentArray[TextDocWithId]([TextDocWithId(id=f'{i}') for i in range(200)])
        assert_all_replicas_indexed(dep, search_da, key='random_num')


@pytest.mark.parametrize('executor_cls', [MyStateExecutor, MyStateExecutorNoSnapshot])
def test_add_new_replica(executor_cls, tmpdir):
    from jina.parsers import set_pod_parser
    from jina.orchestrate.pods.factory import PodFactory
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
    with ctx_mngr:
        index_da = DocumentArray[TextDocWithId](
            [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100)]
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
            index_da = DocumentArray[TextDocWithId](
                [TextDocWithId(id=f'{i}', text=f'ID {i}') for i in range(100, 200)]
            )
            ctx_mngr.index(inputs=index_da, request_size=1, return_type=DocumentArray[TextDocWithId])
            time.sleep(10)
            search_da = DocumentArray[TextDocWithId]([TextDocWithId(id=f'{i}') for i in range(200)])
            client = Client(port=new_replica_port)
            assert_is_indexed(client, search_da=search_da)
