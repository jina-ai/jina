import time

import pytest
import requests as req
from docarray import DocumentArray

from jina import Executor, Flow, requests


class DummyExecutor(Executor):
    @requests(on='/foo')
    def foo(self, docs, **kwargs):
        ...

    @requests(on='/bar')
    def bar(self, docs, **kwargs):
        ...


def test_enable_monitoring_deployment(port_generator):
    port1 = port_generator()
    port2 = port_generator()

    with Flow().add(uses=DummyExecutor, monitoring=True, port_monitoring=port1).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port2
    ) as f:
        for port in [port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        for meth in ['bar', 'foo']:
            f.post(f'/{meth}', inputs=DocumentArray())
            resp = req.get(f'http://localhost:{port2}/')
            assert (
                f'process_request_seconds_created{{executor="DummyExecutor",method="{meth}"}}'
                in str(resp.content)
            )


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_enable_monitoring_gateway(protocol, port_generator):
    port0 = port_generator()
    port1 = port_generator()
    port2 = port_generator()

    with Flow(protocol=protocol, monitoring=True, port_monitoring=port0).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port1
    ).add(uses=DummyExecutor, monitoring=True, port_monitoring=port2) as f:
        for port in [port0, port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port0}/')
        assert f'jina_receiving_request_seconds' in str(resp.content)


def test_monitoring_head(port_generator):
    port1 = port_generator()
    port2 = port_generator()

    with Flow().add(uses=DummyExecutor, monitoring=True, port_monitoring=port1).add(
        uses=DummyExecutor, port_monitoring=port2, monitoring=True, shards=2
    ) as f:
        port3 = f._deployment_nodes['executor0'].pod_args['pods'][0][0].port_monitoring
        port4 = f._deployment_nodes['executor1'].pod_args['pods'][0][0].port_monitoring

        for port in [port1, port2, port3, port4]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200
