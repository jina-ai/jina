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

    with Flow().add(uses=DummyExecutor, port_monitoring=port1, monitoring=True).add(
        uses=DummyExecutor, port_monitoring=port2, monitoring=True
    ) as f:
        for port in [port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        for meth in ['bar', 'foo']:
            f.post(f'/{meth}', inputs=DocumentArray())
            resp = req.get(f'http://localhost:{port2}/')
            assert (
                f'process_request_seconds_created{{endpoint="/{meth}",executor="DummyExecutor"}}'
                in str(resp.content)
            )


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_enable_monitoring_gateway(protocol, port_generator):
    port0 = port_generator()
    port1 = port_generator()
    port2 = port_generator()

    with Flow(protocol=protocol, monitoring=True, port_monitoring=port0).add(
        uses=DummyExecutor, port_monitoring=port1
    ).add(uses=DummyExecutor, port_monitoring=port2) as f:
        for port in [port0, port1, port2]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port0}/')
        assert f'jina_receiving_request_seconds' in str(resp.content)
        assert f'jina_sending_request_seconds' in str(resp.content)


def test_monitoring_head(port_generator):
    port1 = port_generator()
    port2 = port_generator()

    with Flow(monitoring=True).add(uses=DummyExecutor, port_monitoring=port1).add(
        uses=DummyExecutor, port_monitoring=port2, shards=2
    ) as f:
        port3 = f._deployment_nodes['executor0'].pod_args['pods'][0][0].port_monitoring
        port4 = f._deployment_nodes['executor1'].pod_args['pods'][0][0].port_monitoring

        for port in [port1, port2, port3, port4]:
            resp = req.get(f'http://localhost:{port}/')
            assert resp.status_code == 200

        f.search(inputs=DocumentArray())
        resp = req.get(f'http://localhost:{port2}/')
        assert f'jina_receiving_request_seconds' in str(resp.content)
        assert f'jina_sending_request_seconds' in str(resp.content)


def test_document_processed_total(port_generator):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=DummyExecutor, port_monitoring=port1
    ) as f:

        resp = req.get(f'http://localhost:{port1}/')
        assert resp.status_code == 200

        f.post(
            f'/foo', inputs=DocumentArray.empty(size=4)
        )  # process 4 documents on foo

        resp = req.get(f'http://localhost:{port1}/')
        assert (
            f'jina_document_processed_total{{endpoint="/foo",executor="DummyExecutor"}} 4.0'  # check that we count 4 documents on foo
            in str(resp.content)
        )

        assert not (
            f'jina_document_processed_total{{endpoint="/bar",executor="DummyExecutor"}}'  # check that we does not start counting documents on bar as it has not been called yet
            in str(resp.content)
        )

        f.post(
            f'/bar', inputs=DocumentArray.empty(size=5)
        )  # process 5 documents on bar

        assert not (
            f'jina_document_processed_total{{endpoint="/bar",executor="DummyExecutor"}} 5.0'  # check that we count 5 documents on foo
            in str(resp.content)
        )

        assert (
            f'jina_document_processed_total{{endpoint="/foo",executor="DummyExecutor"}} 4.0'  # check that we nothing change on bar count
            in str(resp.content)
        )


def test_disable_monitoring_on_pods(port_generator):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=True, port_monitoring=port0).add(
        uses=DummyExecutor,
        port_monitoring=port1,
        monitoring=False,
    ):
        with pytest.raises(req.exceptions.ConnectionError):  # disable on port1
            resp = req.get(f'http://localhost:{port1}/')

        resp = req.get(f'http://localhost:{port0}/')  # enable on port0
        assert resp.status_code == 200


def test_disable_monitoring_on_gatway_only(port_generator):
    port0 = port_generator()
    port1 = port_generator()

    with Flow(monitoring=False, port_monitoring=port0).add(
        uses=DummyExecutor,
        port_monitoring=port1,
        monitoring=True,
    ):
        with pytest.raises(req.exceptions.ConnectionError):  # disable on port1
            resp = req.get(f'http://localhost:{port0}/')

        resp = req.get(f'http://localhost:{port1}/')  # enable on port0
        assert resp.status_code == 200
