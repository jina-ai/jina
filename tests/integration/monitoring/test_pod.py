import pytest
import requests as req

from jina import Executor, Flow, requests
from jina.helper import random_port


class DummyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print('here')


def test_enable_monitoring_deployment():
    port1 = random_port()
    port2 = random_port()

    with Flow().add(uses=DummyExecutor, monitoring=True, port_monitoring=port1).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port2
    ):
        for port in [port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_enable_monitoring_gateway(protocol):
    port0 = random_port()
    port1 = random_port()
    port2 = random_port()

    with Flow(protocol=protocol, monitoring=True, port_monitoring=port0).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port1
    ).add(uses=DummyExecutor, monitoring=True, port_monitoring=port2):
        for port in [port0, port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200
