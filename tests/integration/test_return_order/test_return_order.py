import random
import time

import pytest

from jina import Client, Document, DocumentArray, Executor, Flow, requests


@pytest.mark.parametrize('stream', [True, False])
@pytest.mark.parametrize('protocol', ['grpc'])
def test_return_order_in_client(protocol, stream):
    class ExecutorRandomSleepExecutor(Executor):
        @requests
        def foo(self, *args, **kwargs):
            rand_sleep = random.uniform(0.1, 1.3)
            time.sleep(rand_sleep)

    f = Flow(protocol=protocol).add(uses=ExecutorRandomSleepExecutor, replicas=2)
    input_text = [f'ordinal-{i}' for i in range(180)]
    input_da = DocumentArray([Document(text=t) for t in input_text])
    with f:
        for _ in range(5):
            result_flow = f.post(
                '/', inputs=input_da, request_size=10, results_in_order=True, stream=stream
            )
            for input, output in zip(input_da, result_flow):
                assert input.text == output.text
        c = Client(port=f.port, protocol=str(f.protocol))
        for _ in range(5):
            result_client = c.post(
                '/', inputs=input_da, request_size=10, results_in_order=True, stream=stream
            )
            for input, output in zip(input_da, result_client):
                assert input.text == output.text
