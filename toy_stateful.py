import os
import time

from jina import Executor, Flow, requests, DocumentArray, Document, Client
from jina.serve.executors.decorators import write
from jina.parsers import set_pod_parser
from jina.orchestrate.pods.factory import PodFactory

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
            self.logger.debug(f' Searching doc {doc.text} against {len(self._docs)} indexed documents')

    def snapshot(self, snapshot_file: str):
        self.logger.warning(f' Snapshotting to {snapshot_file} with {len(self._docs)} documents')
        self.logger.warning(f'Snapshotting with order {[d.text for d in self._docs]}')
        with open(snapshot_file, 'wb') as f:
            self._docs.save_binary(f)

    def restore(self, snapshot_file: str):
        self._docs = DocumentArray.load_binary(snapshot_file)
        self.logger.warning(f' Restoring from {snapshot_file} with {len(self._docs)} documents')
        self.logger.warning(f'Restoring with order {[d.text for d in self._docs]}')


class MyStateExecutorNoSpanshot(Executor):

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
            self.logger.debug(f' Searching doc {doc.text} against {len(self._docs)} indexed documents')


PORT_FLOW_SNAPSHOT = 12340
PORTS_REPLICAS_SNAPSHOT = [12345, 12347, 12349]
PORTS_NEW_REPLICA_SNAPSHOT = 12351
FOLDER_WORKSPACE_SNAPSHOT = './toy_workspace_with_snapshots'

PORT_FLOW_NO_SNAPSHOT = 12360
PORTS_REPLICAS_NO_SNAPSHOT = [12365, 12367, 12369]
PORTS_NEW_REPLICA_NO_SNAPSHOT = 12371
FOLDER_WORKSPACE_NO_SNAPSHOT = './toy_workspace_no_snapshots'

if __name__ == '__main__':
    import sys

    args = sys.argv
    client = None
    index = False
    option = args[1]
    if option == 'index_snapshot':
        f = Flow(port=PORT_FLOW_SNAPSHOT).add(uses=MyStateExecutor,
                                              replicas=3,
                                              # shards=2,
                                              workspace=FOLDER_WORKSPACE_SNAPSHOT,
                                              pod_ports=PORTS_REPLICAS_SNAPSHOT,
                                              stateful=True,
                                              raft_bootstrap=True,
                                              raft_configuration={'snapshot_interval': 10, 'snapshot_threshold': 5, 'trailing_logs': 10,
                                                                  'LogLevel': 'INFO'},
                                              uses_with={'a': 'b'})
        with f:
            f.block()
    elif option == 'index_no_snapshot':
        f = Flow(port=PORT_FLOW_NO_SNAPSHOT).add(uses=MyStateExecutorNoSpanshot,
                                                 replicas=3,
                                                 # shards=2,
                                                 workspace=FOLDER_WORKSPACE_NO_SNAPSHOT,
                                                 pod_ports=PORTS_REPLICAS_NO_SNAPSHOT,
                                                 stateful=True,
                                                 raft_bootstrap=True,
                                                 raft_configuration={'snapshot_interval': 10, 'snapshot_threshold': 5, 'trailing_logs': 10,
                                                                     'LogLevel': 'INFO'})
        f.block()
    elif option == 'restore_snapshot':
        f = Flow(port=PORT_FLOW_SNAPSHOT).add(uses=MyStateExecutor,
                                              replicas=3,
                                              # shards=2,
                                              workspace=FOLDER_WORKSPACE_SNAPSHOT,
                                              pod_ports=PORTS_REPLICAS_SNAPSHOT,
                                              stateful=True,
                                              raft_bootstrap=False,
                                              raft_configuration={'snapshot_interval': 10, 'snapshot_threshold': 5, 'trailing_logs': 10,
                                                                  'LogLevel': 'INFO'})
        with f:
            f.block()
    elif option == 'restore_no_snapshot':
        f = Flow(port=PORT_FLOW_NO_SNAPSHOT).add(uses=MyStateExecutorNoSpanshot,
                                                 replicas=3,
                                                 # shards=2,
                                                 workspace=FOLDER_WORKSPACE_NO_SNAPSHOT,
                                                 pod_ports=PORTS_REPLICAS_NO_SNAPSHOT,
                                                 stateful=True,
                                                 raft_bootstrap=False,
                                                 raft_configuration={'snapshot_interval': 10, 'snapshot_threshold': 5, 'trailing_logs': 10,
                                                                     'LogLevel': 'INFO'})
        with f:
            f.block()
    elif option == 'start_new_replica_snapshot':
        args = set_pod_parser().parse_args([])
        args.host = args.host[0]
        args.port = PORTS_NEW_REPLICA_SNAPSHOT
        args.stateful = True
        args.workspace = FOLDER_WORKSPACE_SNAPSHOT
        args.uses = 'MyStateExecutor'
        args.replica_id = '4'
        with PodFactory.build_pod(args) as p:
            p.join()
    elif option == 'start_new_replica_no_snapshot':
        args = set_pod_parser().parse_args([])
        args.host = args.host[0]
        args.port = PORTS_NEW_REPLICA_NO_SNAPSHOT
        args.stateful = True
        args.workspace = FOLDER_WORKSPACE_NO_SNAPSHOT
        args.uses = 'MyStateExecutorNoSnapshot'
        args.replica_id = '4'
        with PodFactory.build_pod(args) as p:
            p.join()
    elif option == 'add_new_snapshot_replica_to_cluster':
        import jraft
        leader_address = f'0.0.0.0:{PORTS_REPLICAS_SNAPSHOT[0]}'
        voter_address = f'0.0.0.0:{PORTS_NEW_REPLICA_SNAPSHOT}'
        jraft.add_voter(
            leader_address, '4', voter_address
        )
    elif option == 'add_new_no_snapshot_replica_to_cluster':
        import jraft
        leader_address = f'0.0.0.0:{PORTS_REPLICAS_NO_SNAPSHOT[0]}'
        voter_address = f'0.0.0.0:{PORTS_NEW_REPLICA_NO_SNAPSHOT}'
        jraft.add_voter(
            leader_address, '4', voter_address
        )
    elif option == 'client_index_search_snapshot':
        client = Client(port=PORT_FLOW_SNAPSHOT)
        index = True
    elif option == 'client_search_snapshot':
        client = Client(port=PORT_FLOW_SNAPSHOT)
    elif option == 'client_index_search_no_snapshot':
        client = Client(port=PORT_FLOW_NO_SNAPSHOT)
        index = True
    elif option == 'client_search_no_snapshot':
        client = Client(port=PORT_FLOW_NO_SNAPSHOT)
    else:
        print(f' INVALID OPTION {option}')

    if client is not None:
        search_da = DocumentArray([Document(text='SEARCH') for _ in range(10)])
        if index is True:
            index_da = DocumentArray([Document(text=f'ID {i}') for i in range(1000)])
            client.index(inputs=index_da[0:10], request_size=1)
            client.search(inputs=search_da[0:10], request_size=1)
            time.sleep(30)
            client.index(inputs=index_da[10:20], request_size=1)
            client.search(inputs=search_da[0:10], request_size=1)
            time.sleep(30)
            client.index(inputs=index_da[20:30], request_size=1)
            client.search(inputs=search_da[0:10], request_size=1)
            time.sleep(30)
            client.index(inputs=index_da[30:40], request_size=1)
            client.search(inputs=search_da[0:10], request_size=1)
        else:
            client.search(inputs=search_da[0:10], request_size=1)
            client.search(inputs=search_da[0:10], request_size=1)
            client.search(inputs=search_da[0:10], request_size=1)

# JINA_LOG_LEVEL=DEBUG jina executor --uses MyStateExecutor --port 55555 --replica-id '4' --workspace toy_workspace
# --stateful --py-modules toy_stateful.py
