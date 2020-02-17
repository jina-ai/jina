"""The default meta config that all executors follow, they can be overrided by the YAML config

Any executor inherited from :class:`BaseExecutor` always has the following **meta** fields:

    .. confval:: is_trained

        indicates if the executor is trained or not, if not then methods decorated by :func:`@required_train`
        can not be executed.

        :type: bool
        :default: ``False``

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

    .. confval:: work_dir

        the working directory, for dumping and loading serialized executor.

        :type: str
        :default: environment variable :confval:`JINA_EXECUTOR_WORKDIR`, if not set then using current working dir, aka ``cwd``.

    .. confval:: name

        the name of the executor.

        :type: str
        :default: class name plus a random string

    .. confval:: on_gpu

        indicates if the executor is running on GPU.

        :type: bool
        :default: ``False``


    .. confval:: py_modules

        the external python module paths. it is useful when you want to load external python modules
        using :func:`BaseExecutor.load_config` from a YAML file. If a relative path is given then the root path is set to
        the path of the current YAML file.

        :type: str/List[str]
        :default: ``None``


    .. warning::
        ``name`` and ``work_dir`` must be set if you want to serialize/deserialize this executor.



    These **meta** fields can be accessed via `self.is_trained` or loaded from a YAML config via :func:`load_config`:

    .. highlight:: yaml
    .. code-block:: yaml

        !MyAwesomeExecutor
        with:
          ...
        metas:
          name: my_transformer  # a customized name
          is_trained: true  # indicate the model has been trained
          work_dir: ./  # path for serialize/deserialize

.. note::
    The overwrite priority is:

    metas defined in YAML > class attribute > metas.defaults

"""

import os

defaults = {
    'is_trained': False,
    'is_updated': False,
    'batch_size': None,
    'work_dir': os.environ.get('JINA_EXECUTOR_WORKDIR', os.getcwd()),
    'name': None,
    'on_gpu': False,
    'warn_unnamed': os.environ.get('JINA_WARN_UNNAMED', False),
    'max_snapshot': 0,  # deprecated
    'py_modules': None
}
