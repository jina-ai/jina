import multiprocessing
import time
from dataclasses import dataclass

import pytest

from jina import Document, DocumentArray, Executor, requests
from jina.excepts import ExecutorError
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.servers import BaseServer
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
from jina.serve.runtimes.gateway.streamer import GatewayStreamer
from jina.types.request import Request
from jina.types.request.data import DataRequest
from tests.helper import _generate_pod_args


class StreamerTestExecutor(Executor):
    @requests
    def foo(self, docs, parameters, **kwargs):
        text_to_add = parameters.get('text_to_add', 'default ')
        for doc in docs:
            doc.text += text_to_add


def _create_worker_runtime(port, uses, name=''):
    args = _generate_pod_args()
    args.port = [port]
    args.name = name
    args.uses = uses
    with AsyncNewLoopRuntime(args, req_handler_cls=WorkerRequestHandler) as runtime:
        runtime.run_forever()


def _setup(pod0_port, pod1_port):
    pod0_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(pod0_port, 'StreamerTestExecutor')
    )
    pod0_process.start()

    pod1_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(pod1_port, 'StreamerTestExecutor')
    )
    pod1_process.start()

    assert BaseServer.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{pod0_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    assert BaseServer.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{pod1_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    return pod0_process, pod1_process


@pytest.mark.parametrize(
    'parameters, target_executor, expected_text',
    [  # (None, None, 'default default '),
        ({'pod0__text_to_add': 'param_pod0 '}, None, 'param_pod0 default '),
        (None, 'pod1', 'default '),
        ({'pod0__text_to_add': 'param_pod0 '}, 'pod0', 'param_pod0 '),
    ],
)
@pytest.mark.parametrize('results_in_order', [False, True])
@pytest.mark.asyncio
async def test_custom_gateway(
    port_generator, parameters, target_executor, expected_text, results_in_order
):
    pod0_port = port_generator()
    pod1_port = port_generator()
    pod0_process, pod1_process = _setup(pod0_port, pod1_port)
    graph_description = {
        "start-gateway": ["pod0"],
        "pod0": ["pod1"],
        "pod1": ["end-gateway"],
    }
    pod_addresses = {"pod0": [f"0.0.0.0:{pod0_port}"], "pod1": [f"0.0.0.0:{pod1_port}"]}
    # send requests to the gateway
    gateway_streamer = GatewayStreamer(
        graph_representation=graph_description, executor_addresses=pod_addresses
    )
    try:
        input_da = DocumentArray.empty(60)
        resp = DocumentArray.empty(0)
        num_resp = 0
        async for r in gateway_streamer.stream_docs(
            docs=input_da,
            request_size=10,
            parameters=parameters,
            target_executor=target_executor,
            results_in_order=results_in_order,
        ):
            num_resp += 1
            resp.extend(r)

        assert num_resp == 6
        assert len(resp) == 60
        for doc in resp:
            assert doc.text == expected_text

        request = DataRequest()
        request.data.docs = DocumentArray.empty(60)
        unary_response = await gateway_streamer.process_single_data(request=request)
        assert len(unary_response.docs) == 60

    except Exception:
        assert False
    finally:  # clean up runtimes
        pod0_process.terminate()
        pod1_process.terminate()
        pod0_process.join()
        pod1_process.join()
        await gateway_streamer.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('return_results', [False, True])
async def test_gateway_stream_executor_error(port_generator, return_results):
    pod_port = port_generator()
    da = DocumentArray(
        [
            Document(text='Request0'),
            Document(text='Request1'),
            Document(text='Request2'),
        ]
    )

    @dataclass
    class TestExecutor(Executor):
        counter = 0

        @requests
        def foo(self, docs, parameters, **kwargs):
            self.counter += 1
            if self.counter % 2 == 0:
                raise ValueError('custom exception')

    pod_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(pod_port, 'TestExecutor')
    )
    pod_process.start()
    assert BaseServer.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{pod_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )

    graph_description = {
        "start-gateway": ["pod0"],
        "pod0": ["end-gateway"],
    }
    pod_addresses = {"pod0": [f"0.0.0.0:{pod_port}"]}
    # send requests to the gateway
    gateway_streamer = GatewayStreamer(
        graph_representation=graph_description, executor_addresses=pod_addresses
    )

    try:
        responses = []
        errors = []
        async for response, error in gateway_streamer.stream(
            docs=da, request_size=1, return_results=return_results
        ):
            responses.append(response)
            if error:
                errors.append(error)

        assert len(errors) == 1
        error = errors[0]
        assert type(error) == ExecutorError
        assert error.name == 'ValueError'
        assert error.args == ['custom exception']
        assert error.executor == 'TestExecutor'

        if return_results:
            assert all([isinstance(response, Request) for response in responses])
        else:
            assert all([isinstance(response, DocumentArray) for response in responses])
            for index, result_da in enumerate(responses):
                assert da[index] == result_da[0]

    finally:
        pod_process.terminate()
        pod_process.join()
        await gateway_streamer.close()
