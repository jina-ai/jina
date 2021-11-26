import os

from jina import Executor, requests


class EnvExecutor(Executor):
    @requests
    def set_env(self, docs, **kwargs):
        for doc in docs:
            doc.tags['key1'] = os.environ.get('context_var_1')
            doc.tags['key2'] = os.environ.get('context_var_2')
            doc.tags['replicas'] = os.environ.get('num_replicas')
