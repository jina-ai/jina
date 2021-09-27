schema_metas = {
    'Jina::Metas': {
        'description': 'The meta config of the Executor',
        'type': 'object',
        'required': [],
        'additionalProperties': False,
        'properties': {
            'name': {
                'description': 'The name of the executor.',
                'type': 'string',
                'default': None,
            },
            'description': {
                'description': 'The description of this executor. It will be used in automatics docs UI',
                'type': 'string',
                'default': None,
            },
            'py_modules': {
                'type': 'array',
                'default': None,
                'items': {'type': 'string', 'minItems': 1, 'uniqueItems': True},
                'description': '''
The external python module paths. it is useful when you want to load external python modules
using :func:`BaseExecutor.load_config` from a YAML file. If a relative path is given then the root path is set to
the path of the current YAML file.

Example of ``py_module`` usage:

1. This is a valid structure and it is RECOMMENDED:
    - "my_cust_module" is a python module
    - all core logic of your customized executor goes to ``__init__.py``
    - to import ``foo.py``, you can use relative import, e.g. ``from .foo import bar``
    - ``helper.py`` needs to be put BEFORE `__init__.py` in YAML ``py_modules``

This is also the structure given by ``jina hub new`` CLI.

    .. highlight:: text
    .. code-block:: text

         my_cust_module
           |- __init__.py
           |- helper.py
           |- config.yml
                |- py_modules
                       |- helper.py
                       |- __init__.py

2. This is a valid structure but not recommended:
    - "my_cust_module" is not a python module (lack of __init__.py under the root)
    - to import ``foo.py``, you must to use ``from jinahub.foo import bar``
    - ``jinahub`` is a common namespace for all plugin-modules, not changeable.
    - ``helper.py`` needs to be put BEFORE `my_cust.py` in YAML ``py_modules``

    .. highlight:: text
    .. code-block:: text

         my_cust_module
           |- my_cust.py
           |- helper.py
           |- config.yml
                |- py_modules
                       |- helper.py
                       |- my_cust.py                
                ''',
            },
        },
    }
}
