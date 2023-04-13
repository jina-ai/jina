import os
import time
import pytest

from jina import Deployment, Executor, requests, Client, DocumentArray
from jina.helper import random_port


class SingleExecutorDeployment(Executor):

    def __init__(self, init_sleep_time=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        time.sleep(init_sleep_time)

    @requests(on='/foo')
    async def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text += f'return foo {os.getpid()}'
            doc.tags['pid'] = os.getpid()

    @requests(on='/bar')
    async def bar(self, docs, **kwargs):
        for doc in docs:
            doc.text += f'return bar {os.getpid()}'
            doc.tags['pid'] = os.getpid()

    @requests(on='/error')
    async def raise_error(self, docs, **kwargs):
        raise Exception('Raised exception in request')

    @requests(on='/parameters')
    async def return_parameters(self, docs, **kwargs):
        return {'pid': os.getpid()}

    @requests(on='/docsparams')
    async def docs_with_params(self, docs, parameters, **kwargs):
        for doc in docs:
            doc.text = parameters['key']


@pytest.mark.parametrize('replicas', [1, 2, 3])
@pytest.mark.parametrize('include_gateway', [True, False])
@pytest.mark.parametrize('protocols', [['http'], ['grpc', 'http']])
@pytest.mark.parametrize('init_sleep_time', [0, 0.5, 5])
def test_slow_load_executor(replicas, include_gateway, protocols, init_sleep_time):
    if replicas > 1 and not include_gateway:
        return
    ports = [random_port() for _ in range(len(protocols))]
    d = Deployment(uses=SingleExecutorDeployment, uses_with={'init_sleep_time': init_sleep_time}, replicas=replicas,
                   protocol=protocols, port=ports, include_gateway=include_gateway)
    with d:
        for protocol, port in zip(protocols, ports):
            c = Client(protocol=protocol, port=port)
            res = c.post(on='/foo', inputs=DocumentArray.empty(10), request_size=1)
            assert len(res) == 10
            assert all(['foo' in doc.text for doc in res])
            different_pids = set([doc.tags['pid'] for doc in res])
            assert len(different_pids) == replicas
            res = c.post(on='/bar', inputs=DocumentArray.empty(10), request_size=1)
            assert len(res) == 10
            assert all(['bar' in doc.text for doc in res])
            different_pids = set([doc.tags['pid'] for doc in res])
            assert len(different_pids) == replicas


@pytest.mark.parametrize('replicas', [1, 2, 3])
@pytest.mark.parametrize('include_gateway', [True, False])
@pytest.mark.parametrize('protocol', ['grpc', 'http'])
@pytest.mark.parametrize('init_sleep_time', [0, 0.5, 5])
def test_post_from_deployment(replicas, include_gateway, protocol, init_sleep_time):
    if replicas > 1 and not include_gateway:
        return
    d = Deployment(uses=SingleExecutorDeployment, uses_with={'init_sleep_time': init_sleep_time}, replicas=replicas,
                   protocol=protocol, include_gateway=include_gateway)
    with d:
        res = d.post(on='/foo', inputs=DocumentArray.empty(10), request_size=1)
        assert all(['foo' in doc.text for doc in res])
        different_pids = set([doc.tags['pid'] for doc in res])
        assert len(different_pids) == replicas
        res = d.post(on='/bar', inputs=DocumentArray.empty(10), request_size=1)
        assert len(res) == 10
        assert all(['bar' in doc.text for doc in res])
        different_pids = set([doc.tags['pid'] for doc in res])
        assert len(different_pids) == replicas


@pytest.mark.parametrize('replicas', [1, 2, 3])
@pytest.mark.parametrize('include_gateway', [True, False])
@pytest.mark.parametrize('protocols', [['http'], ['grpc', 'http']])
def test_base_executor(replicas, include_gateway, protocols):
    if replicas > 1 and not include_gateway:
        return
    ports = [random_port() for _ in range(len(protocols))]
    d = Deployment(replicas=replicas,
                   protocol=protocols, port=ports, include_gateway=include_gateway)
    with d:
        for protocol, port in zip(protocols, ports):
            c = Client(protocol=protocol, port=port)
            res = c.post(on='/default', inputs=DocumentArray.empty(10), request_size=1)
            assert len(res) == 10


@pytest.mark.parametrize('replicas', [1, 2, 3])
@pytest.mark.parametrize('include_gateway', [True, False])
@pytest.mark.parametrize('protocols', [['http'], ['grpc', 'http']])
@pytest.mark.parametrize('init_sleep_time', [0, 0.5, 5])
def test_return_parameters(replicas, include_gateway, protocols, init_sleep_time):
    if replicas > 1 and not include_gateway:
        return
    ports = [random_port() for _ in range(len(protocols))]
    d = Deployment(uses=SingleExecutorDeployment, uses_with={'init_sleep_time': init_sleep_time}, replicas=replicas,
                   protocol=protocols, port=ports, include_gateway=include_gateway)
    with d:
        for protocol, port in zip(protocols, ports):
            c = Client(protocol=protocol, port=port)
            res = c.post(on='/parameters', inputs=DocumentArray.empty(10), request_size=1, return_responses=True)
            assert len(res) == 10
            assert all(['__results__' in response.parameters.keys() for response in res])
            different_pids = set([list(response.parameters['__results__'].values())[0]['pid'] for response in res])
            assert len(different_pids) == replicas
            res = c.post(on='/docsparams', inputs=DocumentArray.empty(10), parameters={'key': 'value'},
                         request_size=1)
            assert len(res) == 10
            assert all([doc.text == 'value' for doc in res])


@pytest.mark.parametrize('replicas', [1, 2, 3])
@pytest.mark.parametrize('include_gateway', [True, False])
@pytest.mark.parametrize('protocols', [['http'], ['grpc', 'http']])
def test_invalid_protocols_with_shards(replicas, include_gateway, protocols):
    if replicas > 1 and not include_gateway:
        return
    with pytest.raises(RuntimeError):
        d = Deployment(replicas=replicas, protocol=protocols, include_gateway=include_gateway, shards=2)
        with d:
            pass


@pytest.mark.parametrize('replicas', [1, 2, 3])
@pytest.mark.parametrize('include_gateway', [True, False])
@pytest.mark.parametrize('protocols', [['websocket'], ['grpc', 'websocket']])
def test_invalid_websocket_protocol(replicas, include_gateway, protocols):
    if replicas > 1 and not include_gateway:
        return
    with pytest.raises(RuntimeError):
        d = Deployment(replicas=replicas, protocol=protocols, include_gateway=include_gateway)
        with d:
            pass
