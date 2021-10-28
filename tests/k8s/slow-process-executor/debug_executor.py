import os
import time

from jina import Executor, requests, DocumentArray


class SlowProcessExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)

    @requests
    def process(self, docs: DocumentArray, *args, **kwargs):
        time.sleep(1.0)
        for doc in docs:
            doc.tags['replica_uid'] = os.environ['POD_UID']
            doc.tags['time'] = time.time()

        return docs
