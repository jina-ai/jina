import time

import pytest
import requests as req
from prometheus_client import Summary

from jina import Executor, Flow, requests


class DummyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        print('here')


def test_enable_monitoring_deployment():
    port1 = 8089
    port2 = 8090

    with Flow().add(uses=DummyExecutor, monitoring=True, port_monitoring=port1).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port2
    ):
        for port in [port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_enable_monitoring_gateway(protocol):
    port0 = 8088
    port1 = 8089
    port2 = 8090

    with Flow(protocol=protocol, monitoring=True, port_monitoring=port0).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port1
    ).add(uses=DummyExecutor, monitoring=True, port_monitoring=port2):
        for port in [port0, port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200
