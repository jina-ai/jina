import uuid

from jina import Executor, requests


class ScalableExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uid = str(uuid.uuid4())
        self.shard_id = self.runtime_args.shard_id

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['uid'] = self.uid
            doc.tags['shard_id'] = self.shard_id
