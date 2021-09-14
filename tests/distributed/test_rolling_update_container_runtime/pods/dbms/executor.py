from jina import Executor, requests, DocumentArray
from jina.logging.logger import JinaLogger


class DBMSExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()
        self.logger = JinaLogger('IndexExecutor')

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', *args, **kwargs):
        self._docs.extend(docs)

    @requests(on='/dump')
    def dump(self, parameters, *args, **kwargs):
        dump_path = parameters['dump_path']
        self._docs.save(dump_path)
