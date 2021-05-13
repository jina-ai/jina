from jina import requests, Executor


class MergeExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print(f' MERGE EXECUTOR HERE {len(docs)}')
        return docs
