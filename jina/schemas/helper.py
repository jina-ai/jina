def _python_type_to_schema_type(p):
    if p == 'str':
        dtype = 'string'
    elif p == 'int' or p == 'float':
        dtype = 'number'
    elif p in {'typing.List[str]', 'typing.Tuple[str]', 'list', 'tuple'}:
        dtype = 'array'
    elif p == 'bool':
        dtype = 'boolean'
    elif p == 'dict':
        dtype = 'object'
    else:
        dtype = None
        # raise TypeError(f'{p} is not supported')

    return dtype


def _cli_to_schema(
    api_dict,
    target,
    extras=None,
    required=None,
    allow_addition=False,
    namespace='Jina',
    description='',
):
    pod_api = None

    for d in api_dict['methods']:
        if d['name'] == target:
            pod_api = d['options']
            break

    _schema = {
        'properties': {},
        'type': 'object',
        'required': [],
        'additionalProperties': allow_addition,
        'description': description,
    }

    for p in pod_api:
        dtype = _python_type_to_schema_type(p['type'])
        pv = {'description': p['help'].strip(), 'type': dtype, 'default': p['default']}
        if p['choices']:
            pv['enum'] = p['choices']
        if p['required']:
            _schema['required'].append(p['name'])
        if dtype == 'array':
            _schema['items'] = {'type': 'string', 'minItems': 1, 'uniqueItems': True}

        _schema['properties'][p['name']] = pv

    if extras:
        _schema['properties'].update(extras)
    if required:
        _schema['required'].extend(required)

    return {f'{namespace}::{target.capitalize()}': _schema}
