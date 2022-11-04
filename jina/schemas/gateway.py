from jina.schemas.helper import _cli_to_schema
from jina_cli.export import api_to_dict

schema_gateway = _cli_to_schema(
    api_to_dict(),
    ['gateway'],
    allow_addition=False,
    description='The config of a Jina Gateway. A Gateway is a pod that encapsulates Flow logic and exposes services to the internet.',
)
