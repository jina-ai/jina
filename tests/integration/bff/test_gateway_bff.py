import multiprocessing

import pytest

from jina.parsers import set_pod_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from jina.serve.bff import GatewayBFF
from jina import Executor, requests
from jina import DocumentArray


class BffTestExecutor(Executor):

    @requests
    def foo(self, docs, parameters, **kwargs):
        text_to_add = parameters.get('text_to_add', 'default ')
        for doc in docs:
            doc.text += text_to_add


def _create_worker_runtime(port, name=''):
    args = set_pod_parser().parse_args([])
    args.port = port
    args.name = name
    args.uses = 'BffTestExecutor'
    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _setup(pod0_port, pod1_port):
    pod0_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(pod0_port,)
    )
    pod0_process.start()

    pod1_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(pod1_port,)
    )
    pod1_process.start()

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{pod0_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{pod1_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    return pod0_process, pod1_process


@pytest.mark.asyncio
async def test_gateway_bdd(port_generator):
    pod0_port = port_generator()
    pod1_port = port_generator()
    pod0_process, pod1_process = _setup(pod0_port, pod1_port)

    try:
        graph_description = {"start-gateway": ["pod0"], "pod0": ["pod1"], "pod1": ["end-gateway"]}
        pod_addresses = {"pod0": ["0.0.0.0:{pod0_port}"], "pod1": ["0.0.0.0:{pod1_port}"]}
        # send requests to the gateway
        gateway_bff = GatewayBFF(graph_representation=graph_description, executor_addresses=pod_addresses)

        input_da = DocumentArray.empty(60)

        resp = DocumentArray.empty(0)
        num_resp = 0
        async for r in gateway_bff.stream_docs(docs=input_da, request_size=10):
            num_resp += 1
            resp.extend(r)

        assert num_resp == 6
        assert len(resp) == 60
        for doc in resp:
            assert doc.text == 'default default '
    except Exception:
        assert False
    finally:  # clean up runtimes
        pod0_process.terminate()
        pod1_process.terminate()
        pod0_process.join()
        pod1_process.join()



