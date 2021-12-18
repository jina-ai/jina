def _python_type_to_schema_type(p):
    if p == 'str':
        return 'string'
    elif p in ['int', 'float']:
        return 'number'
    elif p in {'typing.List[str]', 'typing.Tuple[str]', 'list', 'tuple'}:
        return 'array'
    elif p == 'bool':
        return 'boolean'
    elif p == 'dict':
        return 'object'
    else:
        return None
            # raise TypeError(f'{p} is not supported')


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
