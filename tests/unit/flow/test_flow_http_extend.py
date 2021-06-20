import pytest

from jina import Executor, requests, Flow


class MyExec(Executor):
    @requests(on='/foo')
    def foo(self, docs, **kwargs):
        pass


def test_flow_debug_endpoints():
    f1 = Flow(protocol='http', no_debug_endpoints=True, no_crud_endpoints=True).add(
        uses=MyExec
    )

    with pytest.raises(ConnectionError):
        with f1:
            f1.post('/foo')

    f2 = Flow(protocol='http', no_crud_endpoints=True).add(uses=MyExec)
    with f2:
        f2.post('/foo')


def test_flow_expose_endpoints():
    f1 = Flow(protocol='http', no_debug_endpoints=True, no_crud_endpoints=True).add(
        uses=MyExec
    )
    import requests

    with f1:
        r = requests.get(f'http://localhost:{f1.port_expose}/foo')
        assert r.status_code == 404

    f1.expose_endpoint('/foo', methods=['POST'])
    with f1:
        r = requests.post(
            f'http://localhost:{f1.port_expose}/foo',
            json={'data': ['hello', 'world']},
        )
        assert r.status_code == 200
