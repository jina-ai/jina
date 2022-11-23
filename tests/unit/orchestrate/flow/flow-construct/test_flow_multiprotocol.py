import itertools

import pytest
from docarray import Document, DocumentArray

from jina import Client, Executor, Flow, requests
from jina.helper import random_port

PROTOCOLS = ['grpc', 'http', 'websocket']


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = 'processed'


@pytest.mark.parametrize(
    'ports,protocols',
    [
        *[
            ([random_port(), random_port(), random_port()], list(protocols))
            for protocols in itertools.permutations(PROTOCOLS, r=3)
        ],
        *[
            ([random_port(), random_port()], list(protocols))
            for protocols in itertools.permutations(PROTOCOLS, r=2)
        ],
        *[
            ([random_port()], list(protocols))
            for protocols in itertools.permutations(PROTOCOLS, r=1)
        ],
    ],
)
def test_flow_multiprotocl(ports, protocols):
    flow = Flow().config_gateway(port=ports, protocol=protocols).add(uses=MyExecutor)

    with flow as f:
        for port, protocol in zip(ports, protocols):
            client = Client(port=port, protocol=protocol)
            docs = client.post('/', inputs=[Document()])
            for doc in docs:
                assert doc.text == 'processed'
