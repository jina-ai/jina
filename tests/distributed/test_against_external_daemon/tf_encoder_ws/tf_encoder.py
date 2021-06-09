from jina import Executor, requests


class TFEncoder(Executor):
    @requests
    def foo(*args, **kwargs):
        import tensorflow

        pass
