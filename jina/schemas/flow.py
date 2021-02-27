from cli.export import api_to_dict
from jina.schemas.helper import _cli_to_schema

schema_flow = _cli_to_schema(
    api_to_dict(),
    'flow',
    extras={
        'jtype': {
            'description': 'The type of Jina object (Flow, Executor, Driver).\n'
                           'A Flow is made up of several sub-tasks, and it manages the states and context of these sub-tasks.\n'
                           'The input and output data of Flows are Documents.',
            'type': 'string',
            'default': 'Flow',
            'enum': ['Flow', 'AsyncFlow']
        },
        'version': {
            'description': 'The YAML version of this Flow.',
            'type': 'string',
            'default': '\'1\'',
        },
        'pods': {
            'description': 'Define the steps in the Flow.\n'
                           'A Pod is a container and interface for one or multiple Peas that have the same properties.',
            'type': 'array',
            'items': {
                '$ref': '#/definitions/Jina::Pod'
            },
            'minItems': 1
        }
    },
    allow_addition=False,
    required=['jtype', 'version', 'pods'])
