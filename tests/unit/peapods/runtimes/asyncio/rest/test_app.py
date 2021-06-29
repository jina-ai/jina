from jina.logging.logger import JinaLogger
from jina.peapods.runtimes.gateway.http import get_fastapi_app
from jina.parsers import set_gateway_parser


def test_custom_swagger():
    args = set_gateway_parser().parse_args(['--custom-swaggerui'])
    logger = JinaLogger('')
    app = get_fastapi_app(args, logger)
    assert any('/docs' in r.path for r in app.routes)
    assert any('/openapi.json' in r.path for r in app.routes)
