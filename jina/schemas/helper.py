import inspect
import re
import typing
from functools import reduce


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


def _get_all_arguments(class_):
    def get_class_arguments(class_):
        """
        :param class_: the class to check
        :return: a list containing the arguments from `class_`
        """
        taboo = {'self', 'args', 'kwargs'}
        signature = inspect.signature(class_.__init__)

        reg = r'.*?:param.*?%s:(.*)'

        class_arguments = {}
        for p in signature.parameters.values():
            if p.name in taboo:
                continue
            class_arguments[p.name] = {}
            if p.default != inspect._empty:
                class_arguments[p.name]['default'] = p.default
            else:
                class_arguments[p.name]['default'] = None
            if p.annotation != inspect._empty:
                dtype = None
                try:
                    if (
                        hasattr(p.annotation, '__origin__')
                        and p.annotation.__origin__ is typing.Union
                    ):
                        dtype = p.annotation.__args__[0].__name__
                    else:
                        dtype = getattr(
                            p.annotation, '__origin__', p.annotation
                        ).__name__
                except:
                    pass
                dtype = _python_type_to_schema_type(dtype)
                if dtype:
                    class_arguments[p.name]['type'] = dtype

            if class_.__init__.__doc__:
                m = re.search(reg % p.name, class_.__init__.__doc__)
                if m and m.group(1):
                    class_arguments[p.name]['description'] = m.group(1).strip()

        return class_arguments

    def accumulate_classes(cls):
        """
        :param cls: the class to check
        :return: all classes from which cls inherits from
        """

        def _accumulate_classes(c, cs):
            cs.append(c)
            if cls == object:
                return cs
            for base in c.__bases__:
                _accumulate_classes(base, cs)
            return cs

        classes = []
        _accumulate_classes(cls, classes)
        return set(classes)

    all_classes = accumulate_classes(class_)
    args = list(map(lambda x: get_class_arguments(x), all_classes))
    return reduce(lambda x, y: {**x, **y}, args)


def _jina_class_to_schema(cls):
    kwargs = _get_all_arguments(cls)

    return {
        'type': 'object',
        'description': cls.__doc__.strip() if cls.__doc__ else '',
        'properties': {
            'jtype': {
                'type': 'string',
                'const': cls.__name__,
                'description': cls.__doc__.strip().split('\n')[0]
                if cls.__doc__
                else '',
            },
            'with': {
                'type': 'object',
                'description': 'The arguments of this Jina Executor',
                'properties': kwargs,
                'additionalProperties': False,
            },
            'metas': {'$ref': '#/definitions/Jina::Metas'},
            'requests': {'$ref': '#/definitions/Jina::Requests'},
        },
        'additionalProperties': False,
    }
