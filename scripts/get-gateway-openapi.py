import json

from jina.parsers import set_gateway_parser
from jina.logging import JinaLogger
from jina.peapods.runtimes.asyncio.rest.app import get_fastapi_app

args = set_gateway_parser().parse_args([])
logger = JinaLogger('')

app = get_fastapi_app(args, logger)
schema = app.openapi()
schema['info']['x-logo'] = {
    'url': 'https://api.jina.ai/logo/logo-product/jina-core/horizontal-layout/colored/Product%20logo_Core_vertical_colorful%402x-margin.png'
}
with open('gateway.json', 'w') as f:
    json.dump(schema, f)
