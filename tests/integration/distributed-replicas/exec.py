import uuid

from jina import Executor, requests


class MyExternalExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = str(uuid.uuid4())

    @requests
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['name'] = self.runtime_args.name
            doc.tags['uuid'] = self._id
