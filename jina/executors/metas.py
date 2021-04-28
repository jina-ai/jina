"""The default meta config that all executors follow, they can be overridden by the YAML config

.. warning::

    When you define your own Executor class, make sure your attributes/methods name do not
    conflict with the name listed below.


.. note::
    Essentially, the meta config can be set in two places: as part of the YAML file, or as the class attribute
    via :func:`__init__` or in class definition. When multiple meta specification exists, the overwrite priority is:

    metas defined in YAML > metas defined as class attribute > metas default values listed below


Any executor inherited from :class:`BaseExecutor` always has the following **meta** fields:

    .. confval:: is_updated

        indicates if the executor is updated or changed since last save, if not then :func:`save` will do nothing.
        A forced save is possible to use :func:`touch` before :func:`save`

        :type: bool
        :default: ``False``

    .. confval:: batch_size

        the size of each batch, methods decorated by :func:`@batching` will respect this. useful when incoming data is
        too large to fit into (GPU) memory.

        :type: int
        :default: ``None``

    .. confval:: workspace

        the working directory, for persisting the artifacts of the executor. An artifact is a file or collection of files
        used during a workflow run.

        By default it is not set, if you expect your executor to be persisted or to persist any data, remember to set it
        to the desired value.

        When a `BaseExecutor` is a component of a `CompoundExecutor`, its `workspace` value will be overridden by the `workspace`
        coming from the `CompoundExecutor` unless a particular `workspace` value is set for the component `BaseExecutor`.

        :type: str
        :default: None

    .. confval:: name

        the name of the executor.

        :type: str
        :default: class name plus a random string

    .. confval:: on_gpu

        if the executor is set to run on GPU.

        :type: bool
        :default: ``False``


    .. confval:: py_modules

        the external python module paths. it is useful when you want to load external python modules
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

        :type: str/List[str]
        :default: ``None``

    .. confval:: pea_id

        the integer index used for distinguish each parallel pea of this executor, required in :attr:`shard_workspace`

        :type: int
        :default: ``'${{root.metas.pea_id}}'``

    .. confval:: root_workspace

        the workspace of the root executor. It will be the same as `executor` except in the case when an `Executor` inside a `CompoundExecutor` is used,
        or when a `BaseNumpyIndexer` is used with a `ref_indexer`.

        By default, jina will try to find if a `dump` of the executor can be found in `workspace`, otherwise it will try to find it under `root_workspace`
        assuming it may be part of a `CompoundExecutor`.

        :type: str
        :default: ``'${{root.metas.workspace}}'``

    .. confval:: root_name

        the name of the root executor. It will be the same as `executor` except in the case when an `Executor` inside a `CompoundExecutor` is used,
        or when a `BaseNumpyIndexer` is used with a `ref_indexer`

        :type: str
        :default: ``'${{root.metas.name}}'``

    .. confval:: read_only

        do not allow the pod to modify the model, save calls will be ignored. If set to true no serialization of the executor

        :type: bool
        :default: ``False``

    .. warning::
        ``name`` and ``workspace`` must be set if you want to serialize/deserialize this executor.

    .. note::

        ``pea_id`` is set in a way that when the executor ``A`` is used as
        a component of a :class:`jina.executors.compound.CompoundExecutor` ``B``, then ``A``'s setting will be overridden by B's counterpart.

    These **meta** fields can be accessed via `self.name` or loaded from a YAML config via :func:`load_config`:

    .. highlight:: yaml
    .. code-block:: yaml

        !MyAwesomeExecutor
        with:
          ...
        metas:
          name: my_transformer  # a customized name
          workspace: ./  # path for serialize/deserialize



"""

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


from typing import Dict, Union, List

_defaults = None


def get_default_metas() -> Dict:
    """
    Get a copy of default meta variables.

    :return: default metas
    """
    import copy

    global _defaults

    if _defaults is None:
        from ..jaml import JAML
        from pkg_resources import resource_stream

        with resource_stream(
            'jina', '/'.join(('resources', 'executors.metas.default.yml'))
        ) as fp:
            _defaults = JAML.load(
                fp
            )  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

    return copy.deepcopy(_defaults)


def fill_metas_with_defaults(d: Dict) -> Dict:
    """Fill the incomplete ``metas`` field with complete default values

    :param d: the loaded YAML map
    :return: dictionary with injected metas
    """

    def _scan(sub_d: Union[Dict, List]):
        if isinstance(sub_d, Dict):
            for k, v in sub_d.items():
                if k == 'metas':
                    _tmp = get_default_metas()
                    _tmp.update(v)
                    sub_d[k] = _tmp
                elif isinstance(v, dict):
                    _scan(v)
                elif isinstance(v, list):
                    _scan(v)
        elif isinstance(sub_d, List):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict):
                    _scan(v)
                elif isinstance(v, list):
                    _scan(v)

    _scan(d)
    return d
