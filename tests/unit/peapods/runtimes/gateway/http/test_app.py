import pytest
import requests as req
from fastapi.testclient import TestClient

from jina import Executor, requests, Flow, DocumentArray
from jina.logging.logger import JinaLogger
from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.gateway.http import get_fastapi_app


@pytest.mark.parametrize('p', [['--default-swagger-ui'], []])
def test_custom_swagger(p):
    args = set_gateway_parser().parse_args(p)
    logger = JinaLogger('')
    app = get_fastapi_app(args, logger)
    # The TestClient is needed here as a context manager to generate the shutdown event correctly
    # otherwise the app can hang as it is not cleaned up correctly
    # see https://fastapi.tiangolo.com/advanced/testing-events/
    with TestClient(app) as client:
        assert any('/docs' in r.path for r in app.routes)
        assert any('/openapi.json' in r.path for r in app.routes)


class TestExecutor(Executor):
    @requests
    def empty(self, docs: 'DocumentArray', **kwargs):
        print(f"# docs {docs}")


@pytest.mark.parametrize(
    'grpc_data_requests',
    [True, False],
)
def test_tag_update(grpc_data_requests):
    PORT_EXPOSE = 33300

    f = Flow(
        port_expose=PORT_EXPOSE,
        protocol='http',
        grpc_data_requests=grpc_data_requests,
    ).add(uses=TestExecutor)

    with f:
        d1 = {"data": [{"id": "1", "prop1": "val"}]}
        d2 = {"data": [{"id": "2", "prop2": "val"}]}
        r1 = req.post(f'http://localhost:{PORT_EXPOSE}/index', json=d1)
        assert r1.json()['data']['docs'][0]['tags'] == {'prop1': 'val'}
        r2 = req.post(f'http://localhost:{PORT_EXPOSE}/index', json=d2)
        assert r2.json()['data']['docs'][0]['tags'] == {'prop2': 'val'}
