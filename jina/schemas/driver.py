from ..importer import IMPORTED

schema_all_drivers = {
    'Jina::Drivers::All': {
        'type': 'array',
        'items': {
            'oneOf': [
                {'$ref': f'#/definitions/{k}'} for k in IMPORTED.schema_drivers.keys()
            ]
        },
        'minItems': 1,
    }
}
