import json

from jina.logging.logger import JinaLogger
from jina.parsers import set_gateway_parser
from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.serve.runtimes.gateway.http.app import get_fastapi_app

JINA_LOGO_URL = 'https://api.jina.ai/logo/logo-product/jina-core/horizontal-layout/colored/Product%20logo_Core_vertical_colorful%402x-margin.png'
GATEWAY_SCHEMA_FILENAME = 'gateway.json'


args = set_gateway_parser().parse_args([])
logger = JinaLogger('')
gateway_app = get_fastapi_app(
    args,
    topology_graph=TopologyGraph({}),
    connection_pool=GrpcConnectionPool(logger=logger),
    logger=logger,
)
gateway_schema = gateway_app.openapi()
gateway_schema['info']['x-logo'] = {'url': JINA_LOGO_URL}
gateway_schema['servers'] = []
gateway_schema['servers'].append(
    {'url': f'http://localhost:{args.port}', 'description': 'Local Jina gateway'}
)
with open(GATEWAY_SCHEMA_FILENAME, 'w') as f:
    json.dump(gateway_schema, f)
