from typing import Optional

from docarray import Document, DocumentArray
from pydantic import BaseModel
from uvicorn import Config, Server

from jina import Gateway
from jina.serve.streamer import GatewayStreamer


class DummyResponseModel(BaseModel):
    arg1: Optional[str]
    arg2: Optional[str]
    arg3: Optional[str]


class ProcessedResponseModel(BaseModel):
    text: str
    tags: Optional[dict]


class DummyGatewayGetStreamer(Gateway):
    def __init__(
        self, arg1: str = None, arg2: str = None, arg3: str = 'default-arg3', **kwargs
    ):
        super().__init__(**kwargs)
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.streamer_obj = GatewayStreamer.get_streamer()

    async def setup_server(self):
        from fastapi import FastAPI

        app = FastAPI(
            title='Dummy Server',
        )

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
            async for docs in self.streamer_obj.stream_docs(
                docs=DocumentArray([Document(text=text)]),
                exec_endpoint='/',
            ):
                doc = docs[0]
            return {'text': doc.text, 'tags': doc.tags}

        self.server = Server(Config(app, host=self.host, port=self.port))

    async def run_server(self):
        await self.server.serve()

    async def shutdown(self):
        self.server.should_exit = True
        await self.server.shutdown()
