from jina import Executor, requests
import os


class ScalableExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_id = os.getpid()
        self.shard_id = self.runtime_args.shard_id

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['shard_id'] = self.shard_id
            doc.tags['process_id'] = self.process_id
