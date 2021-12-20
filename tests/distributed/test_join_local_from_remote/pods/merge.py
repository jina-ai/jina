from jina import Executor, requests


class MergeExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print(f' MERGE EXECUTOR HERE {len(docs)}')
        return docs
