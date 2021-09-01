import os

from typing import Dict, Optional

from jina import Executor, requests, DocumentArray
from jina.logging.logger import JinaLogger


class QueryExecutor(Executor):
    def __init__(self, dump_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger('QueryExecutor')
        self._dump_path = dump_path or kwargs.get('runtime_args', {}).get(
            'dump_path', None
        )
        if self._dump_path is not None and os.path.exists(self._dump_path):
            self.logger.success(f'loading Executor from dump path: {self._dump_path}')
            self._docs = DocumentArray.load(self._dump_path)
        else:
            self.logger.warning(f'no dump path passed. Loading an empty index')
            self._docs = DocumentArray()

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        if len(self._docs) > 0:
            top_k = int(parameters.get('top_k', 5))
            docs.match(self._docs, limit=top_k)
