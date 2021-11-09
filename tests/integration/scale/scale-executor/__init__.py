from jina import Executor, requests


class ScalableExecutor(Executor):
    def __init__(self, allow_failure=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replica_id = self.runtime_args.replica_id
        self.shard_id = self.runtime_args.shard_id
        if self.replica_id > 3 and allow_failure:
            raise Exception(f' I fail when scaling above 4')

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['replica_id'] = self.replica_id
            doc.tags['shard_id'] = self.shard_id
