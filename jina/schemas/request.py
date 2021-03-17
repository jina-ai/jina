__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

schema_requests = {
    'Jina::Requests': {
        'description': 'Define how the Executor behaves under network requests.',
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'use_default': {
                'description': 'If set, then inherit from the default `Driver` settings for this type of Executor.',
                'type': 'boolean',
                'default': False,
            },
            'on': {
                'description': 'Defines how the `Executor` behaves under different types of request',
                'type': 'object',
                'properties': {
                    f'{r_type}Request': {
                        'type': 'object',
                        'properties': {
                            'with': {
                                'type': 'object',
                                'description': 'The common kwargs that all drivers defined under this Request.',
                            },
                            'drivers': {'$ref': f'#/definitions/Jina::Drivers::All'},
                        },
                        'additionalProperties': False,
                        'description': f'Defines how the `Executor` behaves under {r_type} request.',
                    }
                    for r_type in [
                        'Index',
                        'Train',
                        'Search',
                        'Update',
                        'Delete',
                        'Control',
                    ]
                },
                'additionalProperties': False,
            },
        },
    }
}
