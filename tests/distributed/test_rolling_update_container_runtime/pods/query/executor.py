import os

from typing import Optional

from jina import Executor, requests, DocumentArray
from jina.logging.logger import JinaLogger


class QueryExecutor(Executor):
    def __init__(self, dump_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger('QueryExecutor')
        self._dump_path = dump_path
        if self._dump_path is not None and os.path.exists(self._dump_path):
            self._docs = DocumentArray.load(self._dump_path)
        else:
            self._docs = DocumentArray()

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters, **kwargs):
        if len(self._docs) > 0:
            docs.match(self._docs)
