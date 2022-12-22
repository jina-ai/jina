import functools
import os
from typing import Optional

from docarray import Document, DocumentArray
from pydantic import BaseModel
from uvicorn import Config, Server
from werkzeug import run_simple

from jina import Gateway
from jina.helper import get_or_reuse_loop

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'
os.environ['FLASK_DEBUG'] = '1'

from flask import Flask
from uvicorn import Config, Server

from jina import Document, DocumentArray, Executor, Flow, Gateway, requests


class DummyResponseModel(BaseModel):
    arg1: Optional[str]
    arg2: Optional[str]
    arg3: Optional[str]


class ProcessedResponseModel(BaseModel):
    text: str
    tags: Optional[dict]


class DummyGateway(Gateway):
    def __init__(
        self, arg1: str = None, arg2: str = None, arg3: str = 'default-arg3', **kwargs
    ):
        super().__init__(**kwargs)
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3

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
            async for docs in self.streamer.stream_docs(
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

# import psutil

# def get_process_by_name_port(port):
#     processes = [proc for proc in psutil.process_iter()]
#     for p in processes:
#         try:
#             for c in p.connections():
#                 if c.status == 'LISTEN' and c.laddr.port == port:
#                     print(f'found process {p} with port {port}')
#                     return p
#         except:
#             pass
#     return None

class FlaskDummyGateway(Gateway):
    async def setup_server(self):
        # step 1: create an app and define the service endpoint
        app = Flask(__name__)

        @app.route('/service/<input>', methods=['GET'])
        async def my_service(input: str):
            # step 2: convert input request to Documents
            self.streamer._reinit()
            docs = DocumentArray([Document(text=input)])

            # step 3: send Documents to Executors using GatewayStreamer
            result = None
            async for response_docs in self.streamer.stream_docs(
                    docs=docs,
                    exec_endpoint='/',
            ):
                # step 4: convert response docs to server response and return it
                result = response_docs[0].text

            return {'result': result}

        # step 5: implement health-check
        @app.route('/', methods=['GET'])
        def health_check():
            return {}

        # step 6: bind the gateway server to the right port and host

        self.app = app

    async def run_server(self):
        self._loop = get_or_reuse_loop()
        await self._loop.run_in_executor(None, functools.partial(run_simple, hostname=self.host, port=self.port, application=self.app, threaded=False))
        
    async def shutdown(self):
        
        # Attempt 1
        self._loop.shutdown_default_executor()
        self._loop.stop()
        self._loop.close()
        print(self._loop.is_closed())

        # Attempt 2
        # os._exit(0)
        
        # Attempt 3
        # import signal
        # process_python_8080 = get_process_by_name_port(self.port)
        # print(f'kill process {process_python_8080} with port {self.port}')
        # os.kill(process_python_8080.pid, signal.SIGKILL)


class DummyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from DummyExecutor'