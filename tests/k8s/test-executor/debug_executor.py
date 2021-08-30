from typing import Dict

from jina import Executor, requests, DocumentArray


class TestExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)
        self._name = self.runtime_args.name

    @requests(on='/index')
    def debug(self, docs: DocumentArray, parameters: Dict, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )
        key = 'traversed-executors'

        for doc in docs:
            if key not in doc.tags:
                doc.tags[key] = []
            traversed = list(doc.tags.get(key))
            traversed.append(self._name)
            doc.tags[key] = traversed

    @requests(on='/search')
    def read_file(self, docs: DocumentArray, parameters: Dict, **kwargs):
        self.logger.debug(
            f'Received doc array in test-executor {self._name} with length {len(docs)}.'
        )
        key = 'file'
        file_path = '/shared/test_file.txt'

        with open(file_path, 'r') as text_file:
            lines = text_file.readlines()
        for doc in docs:
            doc.tags[key] = lines
