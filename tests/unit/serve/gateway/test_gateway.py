import json
import multiprocessing
import os
import time

import pytest

from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.servers import BaseServer
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler
from tests.helper import (
    _generate_pod_args,
    _validate_custom_gateway_process,
    _validate_dummy_custom_gateway_response,
)
from tests.unit.yaml.dummy_gateway import DummyGateway
from tests.unit.yaml.dummy_gateway_get_streamer import DummyGatewayGetStreamer

cur_dir = os.path.dirname(os.path.abspath(__file__))
_dummy_gateway_yaml_path = os.path.join(cur_dir, '../../yaml/test-custom-gateway.yml')
_dummy_fastapi_gateway_yaml_path = os.path.join(
    cur_dir, '../../yaml/test-fastapi-gateway.yml'
)


def _create_gateway_runtime(port, uses, uses_with, worker_port):
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'
    deployments_metadata = '{"pod0": {"key1": "value1", "key2": "value2"}}'
    with AsyncNewLoopRuntime(
            set_gateway_parser().parse_args(
                [
                    '--port',
                    str(port),
                    '--uses',
                    uses,
                    '--uses-with',
                    json.dumps(uses_with),
                    '--graph-description',
                    graph_description,
                    '--deployments-addresses',
                    pod_addresses,
                    '--deployments-metadata',
                    deployments_metadata,
                ]
            ), req_handler_cls=GatewayRequestHandler
    ) as runtime:
        runtime.run_forever()


def _start_gateway_runtime(uses, uses_with, worker_port):
    port = random_port()

    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(port, uses, uses_with, worker_port),
        daemon=True,
    )
    p.start()
    time.sleep(1)
    return port, p


def _create_worker_runtime(port, uses):
    args = _generate_pod_args(['--uses', uses, '--port', str(port)])

    with AsyncNewLoopRuntime(args, req_handler_cls=WorkerRequestHandler) as runtime:
        runtime.run_forever()


def _start_worker_runtime(uses):
    port = random_port()

    p = multiprocessing.Process(
        target=_create_worker_runtime,
        args=(port, uses),
        daemon=True,
    )
    p.start()
    time.sleep(1)
    return port, p


@pytest.mark.parametrize(
    'uses,uses_with,expected',
    [
        ('DummyGateway', {}, {'arg1': None, 'arg2': None, 'arg3': 'default-arg3'}),
        (
                'DummyGatewayGetStreamer',
                {},
                {'arg1': None, 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
                _dummy_gateway_yaml_path,
                {},
                {'arg1': 'hello', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
                _dummy_fastapi_gateway_yaml_path,
                {},
                {'arg1': 'hello', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
                'DummyGateway',
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
                'DummyGatewayGetStreamer',
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
                _dummy_gateway_yaml_path,
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
                _dummy_fastapi_gateway_yaml_path,
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
                {'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        ),
        (
                'DummyGateway',
                {'arg1': 'arg1'},
                {'arg1': 'arg1', 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
                'DummyGatewayGetStreamer',
                {'arg1': 'arg1'},
                {'arg1': 'arg1', 'arg2': None, 'arg3': 'default-arg3'},
        ),
        (
                _dummy_gateway_yaml_path,
                {'arg1': 'arg1'},
                {'arg1': 'arg1', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
        (
                _dummy_fastapi_gateway_yaml_path,
                {'arg1': 'arg1'},
                {'arg1': 'arg1', 'arg2': 'world', 'arg3': 'default-arg3'},
        ),
    ],
)
def test_custom_gateway_no_executors(uses, uses_with, expected):
    worker_port, worker_process = _start_worker_runtime('ProcessExecutor')
    gateway_port, gateway_process = _start_gateway_runtime(uses, uses_with, worker_port)
    _validate_dummy_custom_gateway_response(gateway_port, expected)
    _validate_custom_gateway_process(
        gateway_port, 'hello', {'text': 'helloworld', 'tags': {'processed': True}}
    )
    gateway_process.terminate()
    gateway_process.join()
    worker_process.terminate()
    worker_process.join()

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0


def test_stream_individual_executor_simple():
    from docarray import DocumentArray, Document

    from jina.serve.runtimes.gateway.http import FastAPIBaseGateway
    from jina import Flow, Executor, requests

    PARAMETERS = {'dog': 'woof'}

    class MyGateway(FastAPIBaseGateway):
        @property
        def app(self):
            from fastapi import FastAPI

            app = FastAPI(title='Custom FastAPI Gateway')

            @app.get('/endpoint')
            async def get(text: str):
                docs = await self.executor['executor1'].post(on='/', inputs=DocumentArray(
                    [Document(text=text), Document(text=text.upper())]), parameters=PARAMETERS)
                return {'result': docs.texts}

            return app

    class FirstExec(Executor):
        @requests
        def func(self, docs, **kwargs):
            for doc in docs:
                doc.text += ' THIS SHOULD NOT HAVE HAPPENED!'

    class SecondExec(Executor):
        @requests
        def func(self, docs, parameters, **kwargs):
            for doc in docs:
                doc.text += f' Second(parameters={str(parameters)})'

    with Flow().config_gateway(uses=MyGateway, protocol='http').add(uses=FirstExec, name='executor0').add(
            uses=SecondExec, name='executor1') as flow:
        import requests
        r = requests.get(f'http://localhost:{flow.port}/endpoint?text=meow')
        assert r.json()['result'] == [f'meow Second(parameters={str(PARAMETERS)})',
                                      f'MEOW Second(parameters={str(PARAMETERS)})']


@pytest.mark.parametrize(
    'n_replicas, n_shards',
    [
        (2, 1),
        (1, 2),
        (2, 2),
    ]
)
def test_stream_individual_executor_multirequest(n_replicas: int, n_shards: int):
    N_DOCS: int = 100
    BATCH_SIZE: int = 5

    from docarray import DocumentArray, Document

    from jina.serve.runtimes.gateway.http import FastAPIBaseGateway
    from jina import Flow, Executor, requests
    import os

    PARAMETERS = {'dog': 'woof'}

    class MyGateway(FastAPIBaseGateway):
        @property
        def app(self):
            from fastapi import FastAPI

            app = FastAPI(title='Custom FastAPI Gateway')

            @app.get('/endpoint')
            async def get(text: str):
                docs = await self.executor['executor1'].post(on='/', inputs=DocumentArray(
                    [Document(text=f'{text} {i}') for i in range(N_DOCS)]), parameters=PARAMETERS,
                                                             request_size=BATCH_SIZE)
                pids = set([doc.tags['pid'] for doc in docs])
                return {'result': docs.texts, 'pids': pids}

            return app

    class FirstExec(Executor):
        @requests
        def func(self, docs, **kwargs):
            for doc in docs:
                doc.text += ' THIS SHOULD NOT HAVE HAPPENED!'

    class SecondExec(Executor):
        @requests
        def func(self, docs, parameters, **kwargs):
            for doc in docs:
                doc.text += f' Second(parameters={str(parameters)})'
                doc.tags['pid'] = os.getpid()

    with Flow().config_gateway(uses=MyGateway, protocol='http').add(uses=FirstExec, name='executor0').add(
            uses=SecondExec, name='executor1', replicas=n_replicas, shards=n_shards
    ) as flow:
        import requests
        r = requests.get(f'http://localhost:{flow.port}/endpoint?text=meow')

        # Make sure the results are correct
        assert set(r.json()['result']) == set([f'meow {i} Second(parameters={str(PARAMETERS)})' for i in range(N_DOCS)])
        # Make sure we are sending to all replicas and shards
        assert len(r.json()['pids']) == n_replicas * n_shards
