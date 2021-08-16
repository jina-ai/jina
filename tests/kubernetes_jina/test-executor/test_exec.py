# Test Executor
from typing import Dict

from jina import Executor, requests, DocumentArray


class TestExecutor(Executor):

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)

    @requests
    def debug(self, docs: DocumentArray, parameters: Dict, **kwargs):
        self.logger.info(f'Received doc array in test-executor {self._name} with length {len(docs)}.')
        for doc in docs:
            if 'traversed-executors' not in doc.tags:
                doc.tags['traversed-executor'] = []
            doc.tags['traversed-executor'].append(self._name)
