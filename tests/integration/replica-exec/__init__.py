import uuid

from jina import Executor, requests


class ReplicatedExec(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uid = str(uuid.uuid4())
        self.shard_id = self.runtime_args.shard_id
        self.shards = self.runtime_args.shards

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['replica'] = self.uid  # identify replicas via uid

            doc.tags['shard_id'] = self.shard_id
            doc.tags['shards'] = self.shards
