from jina import Flow, Executor, requests, Document, DocumentArray, Client
import random
import time

import pytest


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_return_order_in_client(protocol):
    class ExecutorRandomSleepExecutor(Executor):

        @requests
        def foo(self, *args, **kwargs):
            rand_sleep = random.uniform(0.1, 1.3)
            time.sleep(rand_sleep)

    f = Flow(protocol=protocol).add(uses=ExecutorRandomSleepExecutor, replicas=2)
    with f:
        input_text = [f'hey-{i}' for i in range(180)]
        for _ in range(5):
            result_flow = f.post('/', inputs=DocumentArray([Document(text=t) for t in input_text]), request_size=10,  results_in_order=True)
            returned_flow_text = [res.text for res in result_flow]
            for input, output in zip(input_text, returned_flow_text):
                assert input == output
        c = Client(port=f.port, protocol=str(f.protocol))
        for _ in range(5):
            result_client = c.post('/', inputs=DocumentArray([Document(text=t) for t in input_text]), request_size=10, results_in_order=True)
            returned_flow_client = [res.text for res in result_client]
            for input, output in zip(input_text, returned_flow_client):
                assert input == output
