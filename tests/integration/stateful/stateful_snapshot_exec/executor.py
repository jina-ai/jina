from jina import DocumentArray, Executor, requests
from jina.serve.executors.decorators import write
import random

random_pid = random.randint(0, 50000)


class MyStateExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on=['/index'])
    @write
    def index(self, docs, **kwargs):
        for doc in docs:
            self.logger.debug(f'Indexing doc {doc.text}')
            self._docs.append(doc)

    @requests(on=['/search'])
    def search(self, docs, **kwargs):
        for doc in docs:
            doc.text = self._docs[doc.id].text
            doc.tags['pid'] = random_pid

    def snapshot(self, snapshot_file: str):
        self.logger.warning(
            f'Snapshotting to {snapshot_file} with {len(self._docs)} documents'
        )
        self.logger.warning(f'Snapshotting with order {[d.text for d in self._docs]}')
        with open(snapshot_file, 'wb') as f:
            self._docs.save_binary(f)

    def restore(self, snapshot_file: str):
        self._docs = DocumentArray.load_binary(snapshot_file)
        self.logger.warning(
            f'Restoring from {snapshot_file} with {len(self._docs)} documents'
        )
        self.logger.warning(f'Restoring with order {[d.text for d in self._docs]}')
