import os
import time

from jina import Executor, Flow, requests, Document, DocumentArray
from jina.serve.executors.decorators import write

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


class MyStateExecutor(Executor):

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        for doc in docs:
            self.logger.debug(f' Indexing doc {doc.text}')

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        time.sleep(1)
        for doc in docs:
            self.logger.debug(f' Searching doc {doc.text}')


f = Flow().add(uses=MyStateExecutor, ports=[12345, 12347, 12349], replicas=3, stateful=True, workspace='./toy_workspace')

with f:
    #f.block()
    f.index(inputs=DocumentArray([Document(text='INDEX') for _ in range(10)]), request_size=1)
    f.search(inputs=DocumentArray([Document(text='SEARCH') for _ in range(10)]), request_size=1)
    f.block()