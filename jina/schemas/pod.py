from cli.export import api_to_dict

from .helper import _cli_to_schema

schema_pod = _cli_to_schema(
    api_to_dict(),
    'pod',
    extras={
        'needs': {
            'description': 'The name of the Pod(s) that this Pod receives data from. '
            'One can also use `gateway` to '
            'indicate the connection with the gateway.\n'
            'This is useful to create parallelization. '
            'By default the Flow always works sequentially '
            'following the defined order of the Pods.',
            'type': ['array', 'string'],
            'items': {'type': 'string', 'minItems': 1, "uniqueItems": True},
        },
        'method': {
            'description': 'The method to use when appending the Pod to the Flow',
            'type': 'string',
            'enum': ['add', 'needs', 'inspect', 'needs_all', 'gather_inspect'],
            'default': 'add',
        },
    },
    allow_addition=False,
    description='Define the config of a Pod.',
)
