import json

from daemon import _get_app
from daemon.parser import get_main_parser
from jina.logging.logger import JinaLogger
from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.asyncio.http.app import get_fastapi_app


JINA_LOGO_URL = 'https://api.jina.ai/logo/logo-product/jina-core/horizontal-layout/colored/Product%20logo_Core_vertical_colorful%402x-margin.png'
DAEMON_SCHEMA_FILENAME = 'daemon.json'
GATEWAY_SCHEMA_FILENAME = 'gateway.json'


args = set_gateway_parser().parse_args([])
logger = JinaLogger('')
gateway_app = get_fastapi_app(args, logger)
gateway_schema = gateway_app.openapi()
gateway_schema['info']['x-logo'] = {'url': JINA_LOGO_URL}
gateway_schema['servers'] = []
gateway_schema['servers'].append(
    {'url': f'http://localhost:{args.port_expose}', 'description': 'Local Jina gateway'}
)
with open(GATEWAY_SCHEMA_FILENAME, 'w') as f:
    json.dump(gateway_schema, f)


args = get_main_parser().parse_args([])
daemon_app = _get_app()
daemon_schema = daemon_app.openapi()
daemon_schema['info']['x-logo'] = {'url': JINA_LOGO_URL}
daemon_schema['servers'] = []
daemon_schema['servers'].append(
    {'url': f'http://localhost:{args.port_expose}', 'description': 'Local JinaD server'}
)
with open(DAEMON_SCHEMA_FILENAME, 'w') as f:
    json.dump(daemon_schema, f)
