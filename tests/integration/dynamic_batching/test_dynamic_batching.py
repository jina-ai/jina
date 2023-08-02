import asyncio
import multiprocessing
import multiprocessing as mp
import os
import signal
import time
from collections import namedtuple

import pytest

from jina import (
    Client,
    Document,
    DocumentArray,
    Executor,
    Flow,
    dynamic_batching,
    requests,
)
from jina.clients.request import request_generator
from jina.serve.networking.utils import send_request_sync
from jina.serve.runtimes.servers import BaseServer
from jina_cli.api import executor_native
from tests.helper import _generate_pod_args

cur_dir = os.path.dirname(__file__)

TIMEOUT_TOLERANCE = 1
FOO_SUCCESS_MSG = 'Done through foo'
BAR_SUCCESS_MSG = 'Done through bar'


class PlaceholderExecutor(Executor):
    def __init__(self, slow: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.slow = slow

    @requests(on=['/foo'])
    @dynamic_batching(preferred_batch_size=4)
    async def foo_fun(self, docs, **kwargs):
        if self.slow:
            await asyncio.sleep(3)
        for doc in docs:
            doc.text += FOO_SUCCESS_MSG

    @requests(on=['/bar', '/baz'])
    @dynamic_batching(preferred_batch_size=4, timeout=2000)
    async def bar_fun(self, docs, **kwargs):
        if self.slow:
            await asyncio.sleep(3)
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
    async def param_fun(self, docs, parameters, **kwargs):
        if self.slow:
            await asyncio.sleep(3)
        for doc in docs:
            doc.text += str(parameters)


class PlaceholderExecutorWrongDecorator(Executor):
    @requests(on=['/foo'])
    @dynamic_batching(preferred_batch_size=1)
    def foo_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += FOO_SUCCESS_MSG

    @requests(on=['/bar', '/baz'])
    @dynamic_batching(preferred_batch_size=1, timeout=1)
    def bar_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += BAR_SUCCESS_MSG
        return docs

    @requests(on=['/wrongtype'])
    @dynamic_batching(preferred_batch_size=1, timeout=1)
    def wrong_return_type_fun(self, docs, **kwargs):
        return 'Fail me!'

    @requests(on=['/wronglenda'])
    @dynamic_batching(preferred_batch_size=1, timeout=1)
    def wrong_return_lenda_fun(self, docs, **kwargs):
        return DocumentArray.empty(len(docs) + 1)

    @requests(on=['/wronglennone'])
    @dynamic_batching(preferred_batch_size=1, timeout=1)
    def wrong_return_lennone_fun(self, docs, **kwargs):
        docs.append(Document())

    @requests(on=['/param'])
    @dynamic_batching(preferred_batch_size=1, timeout=1)
    def param_fun(self, docs, parameters, **kwargs):
        for doc in docs:
            doc.text += str(parameters)


class PlaceholderExecutorNoDecorators(Executor):
    @requests(on=['/foo'])
    def foo_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += FOO_SUCCESS_MSG

    @requests(on=['/bar', '/baz'])
    def bar_fun(self, docs, **kwargs):
        for doc in docs:
            doc.text += BAR_SUCCESS_MSG
        return docs

    @requests(on=['/wrongtype'])
    def wrong_return_type_fun(self, docs, **kwargs):
        return 'Fail me!'

    @requests(on=['/wronglenda'])
    def wrong_return_lenda_fun(self, docs, **kwargs):
        return DocumentArray.empty(len(docs) + 1)

    @requests(on=['/wronglennone'])
    def wrong_return_lennone_fun(self, docs, **kwargs):
        docs.append(Document())

    @requests(on=['/param'])
    def param_fun(self, docs, parameters, **kwargs):
        for doc in docs:
            doc.text += str(parameters)


class TimeoutExecutor(Executor):
    def __init__(self, sleep: bool = False, **kwargs):
        super(TimeoutExecutor, self).__init__(**kwargs)
        self.sleep = sleep

    @requests(on=['/long_timeout'])
    @dynamic_batching(preferred_batch_size=100, timeout=20000000)
    async def long_timeout_fun(self, docs, parameters, **kwargs):
        if self.sleep:
            await asyncio.sleep(5)
        for doc in docs:
            doc.text += 'long timeout'


USES_DYNAMIC_BATCHING_PLACE_HOLDER_EXECUTOR = {
    '/foo': {'preferred_batch_size': 2, 'timeout': 4000},
    '/bar': {'preferred_batch_size': 4, 'timeout': 2000},
    '/baz': {'preferred_batch_size': 4, 'timeout': 2000},
    '/wrongtype': {'preferred_batch_size': 4, 'timeout': 2000},
    '/wronglenda': {'preferred_batch_size': 4, 'timeout': 2000},
    '/wronglennone': {'preferred_batch_size': 4, 'timeout': 2000},
    '/param': {'preferred_batch_size': 4, 'timeout': 2000},
}

RequestStruct = namedtuple(
    'RequestStruct', ['port', 'endpoint', 'iterator', 'use_stream']
)


def call_api(req: RequestStruct):
    c = Client(port=req.port)
    return c.post(
        req.endpoint,
        inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]),
        stream=req.use_stream,
    )


RequestStructParams = namedtuple(
    'RequestStructParams', ['port', 'endpoint', 'iterator', 'params', 'use_stream']
)


def call_api_with_params(req: RequestStructParams):
    c = Client(port=req.port)
    return c.post(
        req.endpoint,
        inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]),
        parameters=req.params,
        stream=req.use_stream,
    )


@pytest.mark.parametrize(
    'add_parameters',
    [
        {'uses': PlaceholderExecutor},
        {
            'uses': PlaceholderExecutorWrongDecorator,
            'uses_dynamic_batching': USES_DYNAMIC_BATCHING_PLACE_HOLDER_EXECUTOR,
        },
        {
            'uses': PlaceholderExecutorNoDecorators,
            'uses_dynamic_batching': USES_DYNAMIC_BATCHING_PLACE_HOLDER_EXECUTOR,
        },
        {'uses': os.path.join(cur_dir, 'executor-dynamic-batching.yaml')},
        {
            'uses': os.path.join(
                cur_dir, 'executor-dynamic-batching-wrong-decorator.yaml'
            )
        },
    ],
)
@pytest.mark.parametrize('use_stream', [False, True])
def test_timeout(add_parameters, use_stream):
    f = Flow().add(**add_parameters)
    with f:
        start_time = time.time()
        f.post('/bar', inputs=DocumentArray.empty(2), stream=use_stream)
        time_taken = time.time() - start_time
        assert time_taken > 2, 'Timeout ended too fast'
        assert time_taken < 2 + TIMEOUT_TOLERANCE, 'Timeout ended too slowly'

        with mp.Pool(3) as p:
            start_time = time.time()
            list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', range(1), use_stream),
                        RequestStruct(f.port, '/bar', range(1), not use_stream),
                        RequestStruct(f.port, '/bar', range(1), use_stream),
                    ],
                )
            )
            time_taken = time.time() - start_time
            assert time_taken > 2, 'Timeout ended too fast'
            assert time_taken < 2 + TIMEOUT_TOLERANCE, 'Timeout ended too slowly'


@pytest.mark.parametrize(
    'add_parameters',
    [
        {'uses': PlaceholderExecutor},
        {
            'uses': PlaceholderExecutorWrongDecorator,
            'uses_dynamic_batching': USES_DYNAMIC_BATCHING_PLACE_HOLDER_EXECUTOR,
        },
        {
            'uses': PlaceholderExecutorNoDecorators,
            'uses_dynamic_batching': USES_DYNAMIC_BATCHING_PLACE_HOLDER_EXECUTOR,
        },
        {'uses': os.path.join(cur_dir, 'executor-dynamic-batching.yaml')},
        {
            'uses': os.path.join(
                cur_dir, 'executor-dynamic-batching-wrong-decorator.yaml'
            )
        },
    ],
)
@pytest.mark.parametrize('use_stream', [False, True])
def test_preferred_batch_size(add_parameters, use_stream):
    f = Flow().add(**add_parameters)
    with f:
        with mp.Pool(2) as p:
            start_time = time.time()
            list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', range(2), use_stream),
                        RequestStruct(f.port, '/bar', range(2), use_stream),
                    ],
                )
            )
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(2) as p:
            start_time = time.time()
            list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', range(3), use_stream),
                        RequestStruct(f.port, '/bar', range(2), use_stream),
                    ],
                )
            )
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE

        with mp.Pool(4) as p:
            start_time = time.time()
            list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', range(1), use_stream),
                        RequestStruct(f.port, '/bar', range(1), use_stream),
                        RequestStruct(f.port, '/bar', range(1), use_stream),
                        RequestStruct(f.port, '/bar', range(1), use_stream),
                    ],
                )
            )
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE


@pytest.mark.parametrize('use_stream', [False, True])
def test_correctness(use_stream):
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            results = list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', 'ab', use_stream),
                        RequestStruct(f.port, '/bar', 'cd', use_stream),
                    ],
                )
            )
            assert all([len(result) == 2 for result in results])
            assert [doc.text for doc in results[0]] == [
                f'a{BAR_SUCCESS_MSG}',
                f'b{BAR_SUCCESS_MSG}',
            ]
            assert [doc.text for doc in results[1]] == [
                f'c{BAR_SUCCESS_MSG}',
                f'd{BAR_SUCCESS_MSG}',
            ]

        with mp.Pool(2) as p:
            results = list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/foo', 'ABC', use_stream),
                        RequestStruct(f.port, '/foo', 'AB', use_stream),
                    ],
                )
            )
            assert [len(r) for r in results] == [3, 2]
            assert [doc.text for doc in results[0]] == [
                f'A{FOO_SUCCESS_MSG}',
                f'B{FOO_SUCCESS_MSG}',
                f'C{FOO_SUCCESS_MSG}',
            ]
            assert [doc.text for doc in results[1]] == [
                f'A{FOO_SUCCESS_MSG}',
                f'B{FOO_SUCCESS_MSG}',
            ]

        # This is the only one that waits for timeout because its slow
        # But we should still test it at least once
        with mp.Pool(3) as p:
            results = list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', 'a', use_stream),
                        RequestStruct(f.port, '/bar', 'b', use_stream),
                        RequestStruct(f.port, '/bar', 'c', use_stream),
                    ],
                )
            )
            assert all([len(result) == 1 for result in results])
            assert [doc.text for doc in results[0]] == [f'a{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[1]] == [f'b{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[2]] == [f'c{BAR_SUCCESS_MSG}']


@pytest.mark.parametrize('use_stream', [False, True])
def test_incoming_requests_while_flushing(use_stream):
    f = Flow().add(uses=PlaceholderExecutor, uses_with={'slow': True})
    with f:
        with mp.Pool(2) as p:
            # Send 2 concurrent requests. One of them should be flushing and the other one is incoming, but it should
            # not affect the result of the other
            results = list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', 'abcd', use_stream),
                        RequestStruct(f.port, '/bar', 'efg', use_stream),
                    ],
                )
            )
            assert len(results[0]) == 4
            assert len(results[1]) == 3
            assert [doc.text for doc in results[0]] == [
                f'a{BAR_SUCCESS_MSG}',
                f'b{BAR_SUCCESS_MSG}',
                f'c{BAR_SUCCESS_MSG}',
                f'd{BAR_SUCCESS_MSG}',
            ]
            assert [doc.text for doc in results[1]] == [
                f'e{BAR_SUCCESS_MSG}',
                f'f{BAR_SUCCESS_MSG}',
                f'g{BAR_SUCCESS_MSG}',
            ]


@pytest.mark.parametrize('use_stream', [False, True])
def test_param_correctness(use_stream):
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            PARAM = {'key': 'value'}
            results = list(
                p.map(
                    call_api_with_params,
                    [
                        RequestStructParams(f.port, '/param', 'ab', PARAM, use_stream),
                        RequestStructParams(f.port, '/param', 'cd', PARAM, use_stream),
                    ],
                )
            )
            assert all([len(result) == 2 for result in results])
            assert [doc.text for doc in results[0]] == [
                f'a{str(PARAM)}',
                f'b{str(PARAM)}',
            ]
            assert [doc.text for doc in results[1]] == [
                f'c{str(PARAM)}',
                f'd{str(PARAM)}',
            ]

        with mp.Pool(2) as p:
            PARAM1 = {'key1': 'value1'}
            PARAM2 = {'key2': 'value2'}
            results = list(
                p.map(
                    call_api_with_params,
                    [
                        RequestStructParams(
                            f.port, '/param', 'ABCD', PARAM1, use_stream
                        ),
                        RequestStructParams(
                            f.port, '/param', 'ABCD', PARAM2, use_stream
                        ),
                    ],
                )
            )
            assert [len(r) for r in results] == [4, 4]
            assert [doc.text for doc in results[0]] == [
                f'A{str(PARAM1)}',
                f'B{str(PARAM1)}',
                f'C{str(PARAM1)}',
                f'D{str(PARAM1)}',
            ]
            assert [doc.text for doc in results[1]] == [
                f'A{str(PARAM2)}',
                f'B{str(PARAM2)}',
                f'C{str(PARAM2)}',
                f'D{str(PARAM2)}',
            ]

        with mp.Pool(3) as p:
            PARAM1 = {'key1': 'value1'}
            PARAM2 = {'key2': 'value2'}
            results = list(
                p.map(
                    call_api_with_params,
                    [
                        RequestStructParams(
                            f.port, '/param', 'ABC', PARAM1, use_stream
                        ),
                        RequestStructParams(
                            f.port, '/param', 'ABCD', PARAM2, use_stream
                        ),
                        RequestStructParams(f.port, '/param', 'D', PARAM1, use_stream),
                    ],
                )
            )
            assert [len(r) for r in results] == [3, 4, 1]
            assert [doc.text for doc in results[0]] == [
                f'A{str(PARAM1)}',
                f'B{str(PARAM1)}',
                f'C{str(PARAM1)}',
            ]
            assert [doc.text for doc in results[1]] == [
                f'A{str(PARAM2)}',
                f'B{str(PARAM2)}',
                f'C{str(PARAM2)}',
                f'D{str(PARAM2)}',
            ]
            assert [doc.text for doc in results[2]] == [f'D{str(PARAM1)}']

@pytest.mark.parametrize(
    'uses',
    [
        PlaceholderExecutor,
        os.path.join(cur_dir, 'executor-dynamic-batching.yaml'),
        os.path.join(cur_dir, 'executor-dynamic-batching-wrong-decorator.yaml'),
    ],
)
def test_specific_endpoint_batching(uses):
    f = Flow().add(
        uses_dynamic_batching={'/baz': {'preferred_batch_size': 2, 'timeout': 1000}},
        uses=uses,
    )
    with f:
        start_time = time.time()
        f.post('/bar', inputs=DocumentArray.empty(2))
        time_taken = time.time() - start_time
        assert time_taken > 2, 'Timeout ended too fast'
        assert time_taken < 2 + TIMEOUT_TOLERANCE, 'Timeout ended too slowly'

        start_time = time.time()
        f.post('/baz', inputs=DocumentArray.empty(2))
        time_taken = time.time() - start_time
        assert time_taken < TIMEOUT_TOLERANCE, 'Timeout ended too slowly'


def _assert_all_docs_processed(port, num_docs, endpoint):
    resp = send_request_sync(
        _create_test_data_message(num_docs, endpoint=endpoint),
        target=f'0.0.0.0:{port}',
        endpoint=endpoint,
    )
    docs = resp.data.docs
    assert docs.texts == ['long timeout' for _ in range(num_docs)]


def _create_test_data_message(num_docs, endpoint: str = '/'):
    req = list(request_generator(endpoint, DocumentArray.empty(num_docs)))[0]
    return req


@pytest.mark.asyncio
@pytest.mark.parametrize('signal', [signal.SIGTERM, signal.SIGINT])
@pytest.mark.parametrize(
    'uses_with',
    [
        {'sleep': True},
        {'sleep': False},
    ],
)
async def test_sigterm_handling(signal, uses_with):
    import time

    args = _generate_pod_args()

    def run(args):

        args.uses = 'TimeoutExecutor'
        args.uses_with = uses_with
        executor_native(args)

    process = multiprocessing.Process(target=run, args=(args,))
    try:
        process.start()
        time.sleep(2)

        BaseServer.wait_for_ready_or_shutdown(
            timeout=-1,
            ctrl_address=f'{args.host}:{args.port[0]}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        # send request with only 2 docs, not enough to trigger flushing
        # doing this in a new process bc of some pytest vs gRPC weirdness
        with mp.Pool(3) as p:
            results = [
                p.apply_async(
                    _assert_all_docs_processed, (args.port[0], req_size, '/long_timeout')
                )
                for req_size in [10, 20, 30]
            ]

            time.sleep(0.5)

            # send sigterm signal to worker process. This should trigger flushing
            os.kill(process.pid, signal)

            for res in results:
                # wait for results to come
                res.wait()

                # now check that all docs were processed
                assert res.successful()  # no error -> test in each process passed

    finally:
        process.join()

        time.sleep(0.1)


def test_failure_propagation():
    from jina.excepts import BadServer

    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with pytest.raises(BadServer):
            Client(port=f.port).post(
                '/wrongtype',
                inputs=DocumentArray([Document(text=str(i)) for i in range(4)]),
            )
        with pytest.raises(BadServer):
            Client(port=f.port).post(
                '/wrongtype',
                inputs=DocumentArray([Document(text=str(i)) for i in range(2)]),
            )
        with pytest.raises(BadServer):
            Client(port=f.port).post(
                '/wrongtype',
                inputs=DocumentArray([Document(text=str(i)) for i in range(8)]),
            )
        with pytest.raises(BadServer):
            Client(port=f.port).post(
                '/wronglenda',
                inputs=DocumentArray([Document(text=str(i)) for i in range(8)]),
            )
        with pytest.raises(BadServer):
            Client(port=f.port).post(
                '/wronglennone',
                inputs=DocumentArray([Document(text=str(i)) for i in range(8)]),
            )
