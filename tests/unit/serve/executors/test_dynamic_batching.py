from jina import Executor, requests, dynamic_batching, Flow,  DocumentArray, Client
import time
import pytest
import multiprocessing as mp
from collections import namedtuple

TIMEOUT_TOLERANCE = 1
BAR_SUCCESS_MSG = "Done through bar"

class PlaceholderExecutor(Executor):
    @requests
    @dynamic_batching(preferred_batch_size=4)
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Done through foo'
        return docs

    @requests(on=['/bar', '/baz'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def bar_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text = BAR_SUCCESS_MSG
        return docs

def is_processed(da: DocumentArray, success_msg: str) -> bool:
    return all([doc.text == success_msg for doc in da])

RequestStruct = namedtuple('RequestStruct', ['port', 'endpoint', 'num_docs'])
def call_api(req: RequestStruct):
    c = Client(port=req.port)
    return c.post(req.endpoint, inputs=DocumentArray.empty(req.num_docs))

def test_timeout():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        start_time = time.time()
        f.post("/bar", inputs=DocumentArray.empty(2))
        time_taken = time.time() - start_time
        assert time_taken > 2, "Timeout ended too fast"
        assert time_taken < 2 + TIMEOUT_TOLERANCE, "Timeout ended too slowly"
        
        with mp.Pool(3) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
            ]))
            time_taken = time.time() - start_time
            assert time_taken > 2, "Timeout ended too fast"
            assert time_taken < 2 + TIMEOUT_TOLERANCE, "Timeout ended too slowly"


def test_preferred_batch_size():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 2),
                RequestStruct(f.port, "/bar", 2),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(2) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 3),
                RequestStruct(f.port, "/bar", 2),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(4) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

def test_correctness():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 2),
                RequestStruct(f.port, "/bar", 2),
            ]))
            assert all([len(result) == 2 for result in results])
            assert all([is_processed(result, BAR_SUCCESS_MSG) for result in results])

        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 3),
                RequestStruct(f.port, "/bar", 2),
            ]))
            assert [len(r) for r in results] == [3, 2]
            assert all([is_processed(result, BAR_SUCCESS_MSG) for result in results])

        # This is the only one that waits for timeout because its slow
        # But we should still test it at least once
        with mp.Pool(3) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
                RequestStruct(f.port, "/bar", 1),
            ]))
            assert all([len(result) == 1 for result in results])
            assert all([is_processed(result, BAR_SUCCESS_MSG) for result in results])
