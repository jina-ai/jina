from typing import Optional

from docarray import Document, DocumentArray
from pydantic import BaseModel

from jina.clients.request import request_generator
from jina.serve.runtimes.gateway.http import FastAPIBaseGateway


class DummyResponseModel(BaseModel):
    arg1: Optional[str]
    arg2: Optional[str]
    arg3: Optional[str]


class ProcessedResponseModel(BaseModel):
    text: str
    tags: Optional[dict]


class DummyFastAPIGateway(FastAPIBaseGateway):
    def __init__(
        self,
        arg1: str = None,
        arg2: str = None,
        arg3: str = 'default-arg3',
        default_health_check: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.default_health_check = default_health_check

    @property
    def app(self):
        from fastapi import FastAPI

        app = FastAPI(
            title='Dummy Server',
        )

        if not self.default_health_check:

            @app.get(path='/', response_model=DummyResponseModel)
            def _get_response():
                return {
                    'arg1': self.arg1,
                    'arg2': self.arg2,
                    'arg3': self.arg3,
                }

        @app.get(
            path='/stream',
            response_model=ProcessedResponseModel,
        )
        async def _process(text: str):
            doc = None
            async for req in self.streamer.rpc_stream(
                request_generator(
                    exec_endpoint='/',
                    data=DocumentArray([Document(text=text)]),
                )
            ):
                doc = req.to_dict()['data'][0]
            return {'text': doc['text'], 'tags': doc['tags']}

        return app
