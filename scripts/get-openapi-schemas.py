import json

from jina.logging.logger import JinaLogger
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.gateway.http.app import get_fastapi_app

JINA_LOGO_URL = 'https://api.jina.ai/logo/logo-product/jina-core/horizontal-layout/colored/Product%20logo_Core_vertical_colorful%402x-margin.png'
GATEWAY_SCHEMA_FILENAME = 'gateway.json'


args = set_gateway_parser().parse_args([])
logger = JinaLogger('')
gateway_app = get_fastapi_app(
    title=args.title,
    description=args.description,
    no_debug_endpoints=args.no_debug_endpoints,
    no_crud_endpoints=args.no_crud_endpoints,
    expose_endpoints=args.expose_endpoints,
    expose_graphql_endpoint=args.expose_graphql_endpoint,
    cors=args.cors,
    logger=args.logger,
)
gateway_schema = gateway_app.openapi()
gateway_schema['info']['x-logo'] = {'url': JINA_LOGO_URL}
gateway_schema['servers'] = []
gateway_schema['servers'].append(
    {'url': f'http://localhost:{args.port}', 'description': 'Local Jina gateway'}
)
with open(GATEWAY_SCHEMA_FILENAME, 'w') as f:
    json.dump(gateway_schema, f)
