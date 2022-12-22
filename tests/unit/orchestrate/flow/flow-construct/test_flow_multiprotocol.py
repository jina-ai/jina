import itertools
import os.path

import pytest
from docarray import Document, DocumentArray

from jina import Client, Executor, Flow, requests
from jina.helper import random_port

PROTOCOLS = ['grpc', 'http', 'websocket']
cur_dir = os.path.dirname(__file__)


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
            for protocols in itertools.combinations(PROTOCOLS, r=3)
        ],
        *[
            ([random_port(), random_port()], list(protocols))
            for protocols in itertools.combinations(PROTOCOLS, r=2)
        ],
        *[
            ([random_port()], list(protocols))
            for protocols in itertools.combinations(PROTOCOLS, r=1)
        ],
    ],
)
def test_flow_multiprotocol(ports, protocols):
    flow = Flow().config_gateway(port=ports, protocol=protocols).add(uses=MyExecutor)

    with flow:
        for port, protocol in zip(ports, protocols):
            client = Client(port=port, protocol=protocol)
            docs = client.post('/', inputs=[Document()])
            for doc in docs:
                assert doc.text == 'processed'


@pytest.mark.parametrize(
    'protocols',
    [
        list(protocols)
        for protocols in itertools.chain(
            itertools.combinations(PROTOCOLS, r=3),
            itertools.combinations(PROTOCOLS, r=2),
        )
    ],
)
def test_flow_multiprotocol_default_random_ports(protocols):
    flow = Flow().config_gateway(protocol=protocols).add(uses=MyExecutor)

    with flow:
        for port, protocol in zip(flow.port, protocols):
            client = Client(port=port, protocol=protocol)
            docs = client.post('/', inputs=[Document()])
            for doc in docs:
                assert doc.text == 'processed'


@pytest.mark.parametrize(
    'protocols',
    [
        ['grpc'],
        ['http'],
        ['websocket'],
    ],
)
def test_flow_single_protocol_default_random_port(protocols):
    flow = Flow().config_gateway(protocol=protocols).add(uses=MyExecutor)

    with flow:
        for protocol in protocols:
            client = Client(port=flow.port, protocol=protocol)
            docs = client.post('/', inputs=[Document()])
            for doc in docs:
                assert doc.text == 'processed'


def test_flow_multiprotocol_aliases():
    ports = [random_port(), random_port(), random_port()]
    protocols = PROTOCOLS
    flow = Flow().config_gateway(ports=ports, protocols=protocols).add(uses=MyExecutor)

    with flow:
        for port, protocol in zip(ports, protocols):
            client = Client(port=port, protocol=protocol)
            docs = client.post('/', inputs=[Document()])
            for doc in docs:
                assert doc.text == 'processed'


def test_flow_multiprotocol_yaml():
    flow = Flow.load_config(os.path.join(cur_dir, 'yaml/multi-protocol.yml'))

    with flow:
        for port, protocol in zip([12345, 12344, 12343], ['grpc', 'http', 'websocket']):
            client = Client(port=port, protocol=protocol)
            client.post('/', inputs=[Document()])


def test_flow_multiprotocol_ports_protocols_mismatch():
    flow = Flow().config_gateway(port=[random_port()], protocol=['grpc', 'http'])
    with pytest.raises(ValueError) as err_info:
        with flow:
            pass

    assert (
        'You need to specify as much protocols as ports if you want to use a jina built-in gateway'
        in err_info.value.args[0]
    )
