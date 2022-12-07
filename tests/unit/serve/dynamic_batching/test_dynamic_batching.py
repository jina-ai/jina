import multiprocessing
import multiprocessing as mp
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
from jina.parsers import set_gateway_parser, set_pod_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.worker import WorkerRuntime

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

    @requests(on=['/long_timeout'])
    @dynamic_batching(preferred_batch_size=100, timeout=20000000)
    def param_fun(self, docs, parameters, **kwargs):
        for doc in docs:
            doc.text += 'long timeout'


RequestStruct = namedtuple('RequestStruct', ['port', 'endpoint', 'iterator'])


def call_api(req: RequestStruct):
    c = Client(port=req.port)
    return c.post(
        req.endpoint,
        inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]),
    )


RequestStructParams = namedtuple(
    'RequestStructParams', ['port', 'endpoint', 'iterator', 'params']
)


def call_api_with_params(req: RequestStructParams):
    c = Client(port=req.port)
    return c.post(
        req.endpoint,
        inputs=DocumentArray([Document(text=str(i)) for i in req.iterator]),
        parameters=req.params,
    )


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
            list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', range(1)),
                        RequestStruct(f.port, '/bar', range(1)),
                        RequestStruct(f.port, '/bar', range(1)),
                    ],
                )
            )
            time_taken = time.time() - start_time
            assert time_taken > 2, 'Timeout ended too fast'
            assert time_taken < 2 + TIMEOUT_TOLERANCE, 'Timeout ended too slowly'


def test_preferred_batch_size():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            start_time = time.time()
            list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', range(2)),
                        RequestStruct(f.port, '/bar', range(2)),
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
                        RequestStruct(f.port, '/bar', range(3)),
                        RequestStruct(f.port, '/bar', range(2)),
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
                        RequestStruct(f.port, '/bar', range(1)),
                        RequestStruct(f.port, '/bar', range(1)),
                        RequestStruct(f.port, '/bar', range(1)),
                        RequestStruct(f.port, '/bar', range(1)),
                    ],
                )
            )
            time_taken = time.time() - start_time
            assert time_taken < TIMEOUT_TOLERANCE


def test_correctness():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            results = list(
                p.map(
                    call_api,
                    [
                        RequestStruct(f.port, '/bar', 'ab'),
                        RequestStruct(f.port, '/bar', 'cd'),
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
                        RequestStruct(f.port, '/foo', 'ABC'),
                        RequestStruct(f.port, '/foo', 'AB'),
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
                        RequestStruct(f.port, '/bar', 'a'),
                        RequestStruct(f.port, '/bar', 'b'),
                        RequestStruct(f.port, '/bar', 'c'),
                    ],
                )
            )
            assert all([len(result) == 1 for result in results])
            assert [doc.text for doc in results[0]] == [f'a{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[1]] == [f'b{BAR_SUCCESS_MSG}']
            assert [doc.text for doc in results[2]] == [f'c{BAR_SUCCESS_MSG}']


def test_param_correctness():
    f = Flow().add(uses=PlaceholderExecutor)
    with f:
        with mp.Pool(2) as p:
            PARAM = {'key': 'value'}
            results = list(
                p.map(
                    call_api_with_params,
                    [
                        RequestStructParams(f.port, '/param', 'ab', PARAM),
                        RequestStructParams(f.port, '/param', 'cd', PARAM),
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
                        RequestStructParams(f.port, '/param', 'ABCD', PARAM1),
                        RequestStructParams(f.port, '/param', 'ABCD', PARAM2),
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
                        RequestStructParams(f.port, '/param', 'ABC', PARAM1),
                        RequestStructParams(f.port, '/param', 'ABCD', PARAM2),
                        RequestStructParams(f.port, '/param', 'D', PARAM1),
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


def test_specific_endpoint_batching():
    f = Flow().add(
        uses=PlaceholderExecutor,
        uses_dynamic_batching={'/baz': {'preferred_batch_size': 2, 'timeout': 1000}},
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


################
# Helper stuff to build our own Flow in the next test
################


def _create_worker_runtime(port, name='', executor=None):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.uses = 'PlaceholderExecutor'
    args.name = name
    if executor:
        args.uses = executor
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _create_gateway_runtime(
    graph_description, pod_addresses, port, protocol='grpc', retries=-1
):
    with GatewayRuntime(
        set_gateway_parser().parse_args(
            [
                '--graph-description',
                graph_description,
                '--deployments-addresses',
                pod_addresses,
                '--port',
                str(port),
                '--retries',
                str(retries),
                '--protocol',
                protocol,
            ]
        )
    ) as runtime:
        runtime.run_forever()


def _create_worker(port):
    # create a single worker runtime
    p = multiprocessing.Process(target=_create_worker_runtime, args=(port,))
    p.start()
    time.sleep(0.1)
    return p


def _create_gateway(port, graph, pod_addr, protocol, retries=-1):
    # create a single worker runtime
    # create a single gateway runtime
    p = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph, pod_addr, port, protocol, retries),
    )
    p.start()
    time.sleep(0.1)
    return p


def _send_request(gateway_port, num_docs, endpoint):
    """send request to gateway and see what happens"""
    c = Client(host='localhost', port=gateway_port, protocol='grpc')
    res = c.post(endpoint, inputs=DocumentArray.empty(num_docs))
    return res


def _assert_all_docs_processed(gateway_port, num_docs, endpoint):
    res = _send_request(gateway_port, num_docs, endpoint)
    print(f'Got response {res.texts}')
    print(f'Sent {num_docs} docs')
    assert res.texts == ['long timeout' for _ in range(num_docs)]


################
# Helper stuff end
################


def test_sigterm_handling(port_generator):
    try:
        # setup flow by had
        worker_port = port_generator()
        gateway_port = port_generator()
        graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
        pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

        worker_process = _create_worker(worker_port)
        time.sleep(0.1)
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{worker_port}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        gateway_process = _create_gateway(
            gateway_port,
            graph_description,
            pod_addresses,
            'grpc',
        )
        AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
            timeout=5.0,
            ctrl_address=f'0.0.0.0:{gateway_port}',
            ready_or_shutdown_event=multiprocessing.Event(),
        )

        # send request with only 2 docs, not enough to trigger flushing
        # doing this in a new process bc of some pytest vs gRPC weirdness
        assert_all_docs_process = multiprocessing.Process(
            target=_assert_all_docs_processed, args=(gateway_port, 2, '/long_timeout')
        )
        assert_all_docs_process.start()
        time.sleep(0.5)
        # send sigterm signal to worker process. This should trigger flushing
        worker_process.terminate()
        worker_process.join()
        # now check that all docs were processed
        assert (
            assert_all_docs_process.exitcode == 0
        )  # no error -> test in the process passed
    finally:
        # cleanup
        worker_process.kill()
        worker_process.join()
        gateway_process.kill()
        gateway_process.join()
        assert_all_docs_process.kill()
        assert_all_docs_process.join()
