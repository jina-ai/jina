import pytest
from fastapi.testclient import TestClient

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
