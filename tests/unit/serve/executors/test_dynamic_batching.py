from jina import Executor, requests, dynamic_batching, Flow,  DocumentArray, Client, Document
import time
import pytest
import multiprocessing as mp
from collections import namedtuple

TIMEOUT_TOLERANCE = 1
BAR_SUCCESS_MSG = "Done through bar"

class PlaceholderExecutor(Executor):
    @requests
    @dynamic_batching(preferred_batch_size=4)
    def foo_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Done through foo'
        return docs

    @requests(on=['/bar', '/baz'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def bar_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += BAR_SUCCESS_MSG
        return docs

    @requests(on=['/wrongtype'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    def wrong_return_type_fun(self, docs, **kwargs):
        return "Fail me!"

RequestStruct = namedtuple('RequestStruct', ['port', 'endpoint', 'iterator'])
def call_api(req: RequestStruct):
    c = Client(port=req.port)
    return c.post(req.endpoint, inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]))

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
                RequestStruct(f.port, "/bar", range(1)),
                RequestStruct(f.port, "/bar", range(1)),
                RequestStruct(f.port, "/bar", range(1)),
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
                RequestStruct(f.port, "/bar", range(2)),
                RequestStruct(f.port, "/bar", range(2)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(2) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, "/bar", range(3)),
                RequestStruct(f.port, "/bar", range(2)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(4) as p:
            start_time = time.time()
            list(p.map(call_api, [
                RequestStruct(f.port, "/bar", range(1)),
                RequestStruct(f.port, "/bar", range(1)),
                RequestStruct(f.port, "/bar", range(1)),
                RequestStruct(f.port, "/bar", range(1)),
            ]))
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

def test_correctness():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 'ab'),
                RequestStruct(f.port, "/bar", 'cd'),
            ]))
            assert all([len(result) == 2 for result in results])
            assert [doc.text for doc in results[0]] == [f"a{BAR_SUCCESS_MSG}", f"b{BAR_SUCCESS_MSG}"]
            assert [doc.text for doc in results[1]] == [f"c{BAR_SUCCESS_MSG}", f"d{BAR_SUCCESS_MSG}"]

        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 'ABC'),
                RequestStruct(f.port, "/bar", 'AB'),
            ]))
            assert [len(r) for r in results] == [3, 2]
            assert [doc.text for doc in results[0]] == [f"A{BAR_SUCCESS_MSG}", f"B{BAR_SUCCESS_MSG}", f"C{BAR_SUCCESS_MSG}"]
            assert [doc.text for doc in results[1]] == [f"A{BAR_SUCCESS_MSG}", f"B{BAR_SUCCESS_MSG}"]

        # This is the only one that waits for timeout because its slow
        # But we should still test it at least once
        with mp.Pool(3) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/bar", 'a'),
                RequestStruct(f.port, "/bar", 'b'),
                RequestStruct(f.port, "/bar", 'c'),
            ]))
            assert all([len(result) == 1 for result in results])
            assert [doc.text for doc in results[0]] == [f"a{BAR_SUCCESS_MSG}"]
            assert [doc.text for doc in results[1]] == [f"b{BAR_SUCCESS_MSG}"]
            assert [doc.text for doc in results[2]] == [f"c{BAR_SUCCESS_MSG}"]

# The errors are not propagated to the main process or the client
# This is true even without dynamic batching
# So this test is not very useful, just helps with codecov
@pytest.mark.skip(reason="Johannes: Eh its fine")
def test_fail_on_wrong_type():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            results = list(p.map(call_api, [
                RequestStruct(f.port, "/wrongtype", 2),
                RequestStruct(f.port, "/wrongtype", 2),
            ]))
            assert all([len(result) == 2 for result in results])
