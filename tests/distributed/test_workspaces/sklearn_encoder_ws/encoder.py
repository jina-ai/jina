from jina import Executor, requests


class Encoder(Executor):
    @requests
    def foo(*args, **kwargs):
        import sklearn

        pass
