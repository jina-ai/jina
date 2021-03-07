from ..importer import IMPORTED

schema_all_executors = {
    'Jina::Executors::All': {
        'type': 'array',
        'items': {
            'oneOf': [
                {'$ref': f'#/definitions/{k}'} for k in IMPORTED.schema_executors.keys()
            ]
        },
        'minItems': 1,
    }
}
