from jina.logging.logger import JinaLogger
from jina.peapods.runtimes.gateway.http import get_fastapi_app
from jina.parsers import set_gateway_parser
import pytest


@pytest.mark.parametrize('p', [['--default-swagger-ui'], []])
def test_custom_swagger(p):
    args = set_gateway_parser().parse_args(p)
    logger = JinaLogger('')
    app = get_fastapi_app(args, logger)
    assert any('/docs' in r.path for r in app.routes)
    assert any('/openapi.json' in r.path for r in app.routes)
