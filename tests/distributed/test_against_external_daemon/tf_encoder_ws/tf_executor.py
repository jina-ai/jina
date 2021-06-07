from jina import Executor, requests


class TFExecutor(Executor):
    @requests
    def foo(*args, **kwargs):
        import tensorflow
        pass
