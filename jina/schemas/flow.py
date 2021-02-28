from cli.export import api_to_dict
from jina.schemas.helper import _cli_to_schema

_schema_flow_with = _cli_to_schema(
    api_to_dict(),
    'flow',
    allow_addition=False,
    description='The config of Flow, unrecognized config arguments will be applied to all Pods')['Jina::Flow']

schema_flow = {
    'Jina::Flow': {
        'properties': {
            'with': _schema_flow_with,
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
        'type': 'object',
        'additionalProperties': False,
        'required': ['jtype', 'version', 'pods'],
    }}
