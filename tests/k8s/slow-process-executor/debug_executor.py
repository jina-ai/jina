import os
import time

from jina import Executor, requests, DocumentArray


class SlowProcessExecutor(Executor):
    def __init__(self, time_sleep=1.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_sleep = time_sleep

    @requests
    def process(self, docs: DocumentArray, *args, **kwargs):
        time.sleep(self.time_sleep)
        for doc in docs:
            doc.tags['replica_uid'] = os.environ['POD_UID']
            doc.tags['time'] = time.time()

        return docs
