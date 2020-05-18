from . import BaseExecutor


class BaseClientExecutor(BaseExecutor):
    def __init__(self, host=None, port=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port


class TFServingClientExecutor(BaseClientExecutor):
    pass


