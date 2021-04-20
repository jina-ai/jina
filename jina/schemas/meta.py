schema_metas = {
    'Jina::Metas': {
        'description': 'The meta config of the Executor',
        'type': 'object',
        'required': [],
        'additionalProperties': False,
        'properties': {
            'is_updated': {
                'description': 'Indicates if the executor is updated or changed since last save. '
                'If not, then save() will do nothing. A forced save is possible to use `touch()` before `save()`',
                'type': 'boolean',
                'default': False,
            },
            'batch_size': {
                'description': 'The size of each batch, methods decorated by `@batching` will respect this. '
                'Useful when incoming data is too large to fit into (GPU) memory.',
                'type': 'number',
                'default': None,
            },
            'workspace': {
                'description': '''
The working directory, for persisting the artifacts of the executor. An artifact is a file or collection of files used during a workflow run.

By default it is not set, if you expect your executor to be persisted or to persist any data, remember to set it to the desired value.

When a BaseExecutor is a component of a `CompoundExecutor`, its workspace value will be overridden by the workspace coming from the `CompoundExecutor` unless a particular workspace value is set for the component BaseExecutor.                
                ''',
                'type': 'string',
                'default': None,
            },
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
            'read_only': {
                'description': 'Do not allow the Pod to modify the Executor, save calls will be ignored. '
                'If set to true no serialization of the Executor',
                'type': 'boolean',
                'default': False,
            },
            'on_gpu': {
                'description': 'If the executor is set to run on GPU.',
                'type': 'boolean',
                'default': False,
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
