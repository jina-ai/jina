import os
import time

from docarray import DocumentArray, Executor, requests


class TagTextExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pod_uid = os.environ['POD_UID']

    @requests
    def process(self, docs: DocumentArray, *args, **kwargs):
        for doc in docs:
            doc.tags['replica_uid'] = self.pod_uid
            doc.tags['time'] = time.time()
            doc.text += f'_{self.pod_uid}'

        return docs
