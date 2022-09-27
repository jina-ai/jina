from jina.serve.gateway import BaseGateway


class DummyGateway(BaseGateway):
    def __init__(
        self, arg1: str = None, arg2: str = None, arg3: str = 'default-arg3', **kwargs
    ):
        super().__init__(**kwargs)
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3

    async def setup_server(self):
        pass

    async def run_server(self):
        pass

    async def teardown(self):
        pass

    async def stop_server(self):
        pass
