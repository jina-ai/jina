import os
import time

from jina import Executor, Flow, requests, Document, DocumentArray
from jina.serve.executors.decorators import write

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


class MyStateExecutor(Executor):

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        time.sleep(0.2)
        for doc in docs:
            self.logger.debug(f' Indexing doc {doc.text}')

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        time.sleep(0.2)
        for doc in docs:
            self.logger.debug(f' Searching doc {doc.text}')


f = Flow().add(uses=MyStateExecutor, replicas=3, shards=2, workspace='./toy_workspace', stateful=True,
               raft_bootstrap=True, raft_configuration={'snapshot_interval': 300000, 'LogLevel': 'INFO'})

with f:
    # f.block()
    f.index(inputs=DocumentArray([Document(text='INDEX') for _ in range(10)]), request_size=1)
    f.search(inputs=DocumentArray([Document(text='SEARCH') for _ in range(10)]), request_size=1)
    f.block()
