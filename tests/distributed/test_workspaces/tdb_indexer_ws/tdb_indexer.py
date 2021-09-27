from jina import Executor, requests


class TinyDBIndexer(Executor):
    @requests
    def foo(*args, **kwargs):
        from tinydb import TinyDB, Query

        pass
