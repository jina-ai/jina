from jina import Executor, requests, dynamic_batching, Flow,  DocumentArray, Client, Document
import time
import pytest
import multiprocessing as mp
from collections import namedtuple

TIMEOUT_TOLERANCE = 1
FOO_SUCCESS_MSG = 'Done through foo'
BAR_SUCCESS_MSG = 'Done through bar'

class PlaceholderExecutor(Executor):
    @requests(on=['/foo'])
    @dynamic_batching(preferred_batch_size=4)
    def foo_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += FOO_SUCCESS_MSG

    @requests(on=['/bar', '/baz'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def bar_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += BAR_SUCCESS_MSG
        return docs

    @requests(on=['/wrongtype'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def wrong_return_type_fun(self, docs, **kwargs):
        return 'Fail me!'

    @requests(on=['/wronglenda'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def wrong_return_lenda_fun(self, docs, **kwargs):
        return DocumentArray.empty(len(docs) + 1)

    @requests(on=['/wronglennone'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def wrong_return_lennone_fun(self, docs, **kwargs):
        docs.append(Document())
    
    @requests(on=['/param'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def param_fun(self, docs, parameters, **kwargs):
        for doc in docs:
            doc.text += str(parameters)

RequestStruct = namedtuple('RequestStruct', ['port', 'endpoint', 'iterator'])
def call_api(req: RequestStruct):
    c = Client(port=req.port)
    return c.post(req.endpoint, inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]))

RequestStructParams = namedtuple('RequestStructParams', ['port', 'endpoint', 'iterator', 'params'])
def call_api_with_params(req: RequestStructParams):
    c = Client(port=req.port)
    return c.post(req.endpoint, inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]), parameters=req.params)

def test_timeout():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        start_time = time.time()
        f.post('/bar', inputs=DocumentArray.empty(2))
        time_taken = time.time() - start_time
        assert time_taken > 2, 'Timeout ended too fast'
        assert time_taken < 2 + TIMEOUT_TOLERANCE, 'Timeout ended too slowly'
        
        with mp.Pool(3) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, '/bar', range(1)),
                RequestStruct(f.port, '/bar', range(1)),
                RequestStruct(f.port, '/bar', range(1)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken > 2, 'Timeout ended too fast'
            assert time_taken < 2 + TIMEOUT_TOLERANCE, 'Timeout ended too slowly'


def test_preferred_batch_size():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, '/bar', range(2)),
                RequestStruct(f.port, '/bar', range(2)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(2) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, '/bar', range(3)),
                RequestStruct(f.port, '/bar', range(2)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(4) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, '/bar', range(1)),
                RequestStruct(f.port, '/bar', range(1)),
                RequestStruct(f.port, '/bar', range(1)),
                RequestStruct(f.port, '/bar', range(1)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE


def test_correctness():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, '/bar', 'ab'),
                RequestStruct(f.port, '/bar', 'cd'),
            ]))
            assert all([len(result) == 2 for result in results])
            assert [doc.text for doc in results[0]] == [f'a{BAR_SUCCESS_MSG}', f'b{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[1]] == [f'c{BAR_SUCCESS_MSG}', f'd{BAR_SUCCESS_MSG}']

        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, '/foo', 'ABC'),
                RequestStruct(f.port, '/foo', 'AB'),
            ]))
            assert [len(r) for r in results] == [3, 2]
            assert [doc.text for doc in results[0]] == [f'A{FOO_SUCCESS_MSG}', f'B{FOO_SUCCESS_MSG}', f'C{FOO_SUCCESS_MSG}']
            assert [doc.text for doc in results[1]] == [f'A{FOO_SUCCESS_MSG}', f'B{FOO_SUCCESS_MSG}']

        # This is the only one that waits for timeout because its slow
        # But we should still test it at least once
        with mp.Pool(3) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, '/bar', 'a'),
                RequestStruct(f.port, '/bar', 'b'),
                RequestStruct(f.port, '/bar', 'c'),
            ]))
            assert all([len(result) == 1 for result in results])
            assert [doc.text for doc in results[0]] == [f'a{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[1]] == [f'b{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[2]] == [f'c{BAR_SUCCESS_MSG}']


def test_param_correctness():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            PARAM = {'key': 'value'}
            results = list(p.map(call_api_with_params, [
                RequestStructParams(f.port, '/param', 'ab', PARAM),
                RequestStructParams(f.port, '/param', 'cd', PARAM),
            ]))
            assert all([len(result) == 2 for result in results])
            assert [doc.text for doc in results[0]] == [f'a{str(PARAM)}', f'b{str(PARAM)}']
            assert [doc.text for doc in results[1]] == [f'c{str(PARAM)}', f'd{str(PARAM)}']

        with mp.Pool(2) as p:
            PARAM1 = {'key1': 'value1'}
            PARAM2 = {'key2': 'value2'}
            results = list(p.map(call_api_with_params, [
                RequestStructParams(f.port, '/param', 'ABCD', PARAM1),
                RequestStructParams(f.port, '/param', 'ABCD', PARAM2),
            ]))
            assert [len(r) for r in results] == [4, 4]
            assert [doc.text for doc in results[0]] == [f'A{str(PARAM1)}', f'B{str(PARAM1)}', f'C{str(PARAM1)}', f'D{str(PARAM1)}']
            assert [doc.text for doc in results[1]] == [f'A{str(PARAM2)}', f'B{str(PARAM2)}', f'C{str(PARAM2)}', f'D{str(PARAM2)}']

        with mp.Pool(3) as p:
            PARAM1 = {'key1': 'value1'}
            PARAM2 = {'key2': 'value2'}
            results = list(p.map(call_api_with_params, [
                RequestStructParams(f.port, '/param', 'ABC', PARAM1),
                RequestStructParams(f.port, '/param', 'ABCD', PARAM2),
                RequestStructParams(f.port, '/param', 'D', PARAM1),
            ]))
            assert [len(r) for r in results] == [3, 4, 1]
            assert [doc.text for doc in results[0]] == [f'A{str(PARAM1)}', f'B{str(PARAM1)}', f'C{str(PARAM1)}']
            assert [doc.text for doc in results[1]] == [f'A{str(PARAM2)}', f'B{str(PARAM2)}', f'C{str(PARAM2)}', f'D{str(PARAM2)}']
            assert [doc.text for doc in results[2]] == [f'D{str(PARAM1)}']


def test_failure_propagation():
    from jina.excepts import BadServer
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with pytest.raises(BadServer):
            Client(port=f.port).post('/wrongtype', inputs=DocumentArray([Document(text=str(i)) for i in range(4)]))
        with pytest.raises(BadServer):
            Client(port=f.port).post('/wrongtype', inputs=DocumentArray([Document(text=str(i)) for i in range(2)]))
        with pytest.raises(BadServer):
            Client(port=f.port).post('/wrongtype', inputs=DocumentArray([Document(text=str(i)) for i in range(8)]))
        with pytest.raises(BadServer):
            Client(port=f.port).post('/wronglenda', inputs=DocumentArray([Document(text=str(i)) for i in range(8)]))
        with pytest.raises(BadServer):
            Client(port=f.port).post('/wronglennone', inputs=DocumentArray([Document(text=str(i)) for i in range(8)]))
