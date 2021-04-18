__copyright__ = 'Copyright (c) 2020 Jina AI Limited. All rights reserved.'
__license__ = 'Apache-2.0'

import os
import pickle
import tempfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, TypeVar, Type, List, Optional

from .decorators import (
    as_update_method,
    store_init_kwargs,
    as_aggregate_method,
    wrap_func,
)
from .metas import get_default_metas, fill_metas_with_defaults
from ..excepts import BadPersistantFile, NoDriverForRequest, UnattachedDriver
from ..helper import typename, random_identity
from ..jaml import JAMLCompatible, JAML, subvar_regex, internal_var_regex
from ..logging import JinaLogger
from ..logging.profile import TimeContext

if False:
    from ..peapods.runtimes.zmq.zed import ZEDRuntime
    from ..drivers import BaseDriver

__all__ = ['BaseExecutor', 'AnyExecutor', 'ExecutorType']

AnyExecutor = TypeVar('AnyExecutor', bound='BaseExecutor')

# some variables may be self-referred and they must be resolved at here
_ref_desolve_map = SimpleNamespace()
_ref_desolve_map.__dict__['metas'] = SimpleNamespace()
_ref_desolve_map.__dict__['metas'].__dict__['pea_id'] = 0


class ExecutorType(type(JAMLCompatible), type):
    """The class of Executor type, which is the metaclass of :class:`BaseExecutor`."""

    def __new__(cls, *args, **kwargs):
        """


        # noqa: DAR201


        # noqa: DAR101


        # noqa: DAR102
        """
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    def __call__(cls, *args, **kwargs):
        """


        # noqa: DAR201


        # noqa: DAR101


        # noqa: DAR102
        """
        # do _preload_package
        getattr(cls, 'pre_init', lambda *x: None)()

        m = kwargs.pop('metas') if 'metas' in kwargs else {}
        r = kwargs.pop('requests') if 'requests' in kwargs else {}

        obj = type.__call__(cls, *args, **kwargs)

        # set attribute with priority
        # metas in YAML > class attribute > default_jina_config
        # jina_config = expand_dict(jina_config)

        getattr(obj, '_post_init_wrapper', lambda *x: None)(m, r)
        return obj

    @staticmethod
    def register_class(cls):
        """
        Register a class and wrap update, train, aggregate functions.

        :param cls: The class.
        :return: The class, after being registered.
        """
        update_funcs = ['add', 'delete', 'update']
        aggregate_funcs = ['evaluate']

        reg_cls_set = getattr(cls, '_registered_class', set())

        cls_id = f'{cls.__module__}.{cls.__name__}'
        if cls_id not in reg_cls_set or getattr(cls, 'force_register', False):
            wrap_func(cls, ['__init__'], store_init_kwargs)
            wrap_func(cls, update_funcs, as_update_method)
            wrap_func(cls, aggregate_funcs, as_aggregate_method)

            reg_cls_set.add(cls_id)
            setattr(cls, '_registered_class', reg_cls_set)
        return cls


class BaseExecutor(JAMLCompatible, metaclass=ExecutorType):
    """
    The base class of the executor, can be used to build encoder, indexer, etc.

    Any executor inherited from :class:`BaseExecutor` always has the **meta** defined in :mod:`jina.executors.metas.defaults`.

    All arguments in the :func:`__init__` can be specified with a ``with`` map in the YAML config. Example:

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeExecutor:
            def __init__(awesomeness = 5):
                pass

    is equal to

    .. highlight:: yaml
    .. code-block:: yaml

        !MyAwesomeExecutor
        with:
            awesomeness: 5

    To use an executor in a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`,
    a proper :class:`jina.drivers.Driver` is required. This is because the
    executor is *NOT* protobuf-aware and has no access to the key-values in the protobuf message.

    Different executor may require different :class:`Driver` with
    proper :mod:`jina.drivers.handlers`, :mod:`jina.drivers.hooks` installed.

    .. seealso::
        Methods of the :class:`BaseExecutor` can be decorated via :mod:`jina.executors.decorators`.

    .. seealso::
        Meta fields :mod:`jina.executors.metas.defaults`.

    """

    store_args_kwargs = False  #: set this to ``True`` to save ``args`` (in a list) and ``kwargs`` (in a map) in YAML config
    exec_methods = [
        'encode',
        'add',
        'query',
        'craft',
        'segment',
        'score',
        'evaluate',
        'predict',
        'query_by_key',
        'delete',
        'update',
        # TODO make Dump a control request to be passed to the Pod directly
        'dump',
    ]

    def __init__(self, *args, **kwargs):
        if isinstance(args, tuple) and len(args) > 0:
            self.args = args[0]
        else:
            self.args = args
        self.logger = JinaLogger(self.__class__.__name__)
        self._snapshot_files = []
        self._post_init_vars = set()
        self._last_snapshot_ts = datetime.now()

    def _post_init_wrapper(
        self,
        _metas: Optional[Dict] = None,
        _requests: Optional[Dict] = None,
        fill_in_metas: bool = True,
    ) -> None:
        if fill_in_metas:
            if not _metas:
                _metas = get_default_metas()

            self._fill_metas(_metas)
            self.fill_in_drivers(_requests)

        _before = set(list(vars(self).keys()))
        self.post_init()
        self._post_init_vars = {k for k in vars(self) if k not in _before}

    def fill_in_drivers(self, _requests: Optional[Dict]):
        """
        Fill in drivers in a BaseExecutor.

        :param _requests: Dict containing driver information.
        """
        from ..executors.requests import get_default_reqs

        default_requests = get_default_reqs(type.mro(self.__class__))

        if not _requests:
            self._drivers = self._get_drivers_from_requests(default_requests)
        else:
            parsed_drivers = self._get_drivers_from_requests(_requests)

            if _requests.get('use_default', False):
                default_drivers = self._get_drivers_from_requests(default_requests)

                for k, v in default_drivers.items():
                    if k not in parsed_drivers:
                        parsed_drivers[k] = v

            self._drivers = parsed_drivers

    @staticmethod
    def _get_drivers_from_requests(_requests):
        _drivers = {}  # type: Dict[str, List['BaseDriver']]

        if _requests and 'on' in _requests and isinstance(_requests['on'], dict):
            # if control request is forget in YAML, then fill it
            if 'ControlRequest' not in _requests['on']:
                from ..drivers.control import ControlReqDriver

                _requests['on']['ControlRequest'] = [ControlReqDriver()]

            for req_type, drivers_spec in _requests['on'].items():
                if isinstance(req_type, str):
                    req_type = [req_type]
                if isinstance(drivers_spec, list):
                    # old syntax
                    drivers = drivers_spec
                    common_kwargs = {}
                elif isinstance(drivers_spec, dict):
                    drivers = drivers_spec.get('drivers', [])
                    common_kwargs = drivers_spec.get('with', {})
                else:
                    raise TypeError(f'unsupported type of driver spec: {drivers_spec}')

                for r in req_type:
                    if r not in _drivers:
                        _drivers[r] = list()
                    if _drivers[r] != drivers:
                        _drivers[r].extend(drivers)

                    # inject common kwargs to drivers
                    if common_kwargs:
                        new_drivers = []
                        for d in _drivers[r]:
                            new_init_kwargs_dict = {
                                k: v for k, v in d._init_kwargs_dict.items()
                            }
                            new_init_kwargs_dict.update(common_kwargs)
                            new_drivers.append(d.__class__(**new_init_kwargs_dict))
                        _drivers[r].clear()
                        _drivers[r] = new_drivers

                    if not _drivers[r]:
                        _drivers.pop(r)

        return _drivers

    def _fill_metas(self, _metas):
        unresolved_attr = False
        # set self values filtered by those non-exist, and non-expandable
        for k, v in _metas.items():
            if not hasattr(self, k):
                if isinstance(v, str):
                    if not subvar_regex.findall(v):
                        setattr(self, k, v)
                    else:
                        unresolved_attr = True
                else:
                    setattr(self, k, v)
            elif type(getattr(self, k)) == type(v):
                setattr(self, k, v)
        if not getattr(self, 'name', None):
            _id = random_identity().split('-')[0]
            _name = f'{typename(self)}-{_id}'
            if getattr(self, 'warn_unnamed', False):
                self.logger.warning(
                    f'this executor is not named, i will call it "{_name}". '
                    'naming is important as it provides an unique identifier when '
                    'persisting this executor on disk.'
                )
            setattr(self, 'name', _name)
        if unresolved_attr:
            _tmp = vars(self)
            _tmp['metas'] = _metas
            new_metas = JAML.expand_dict(_tmp, context=_ref_desolve_map)['metas']

            # set self values filtered by those non-exist, and non-expandable
            for k, v in new_metas.items():
                if not hasattr(self, k):
                    if isinstance(v, str):
                        if not (
                            subvar_regex.findall(v) or internal_var_regex.findall(v)
                        ):
                            setattr(self, k, v)
                        else:
                            raise ValueError(
                                f'{k}={v} is not substitutable or badly referred'
                            )
                    else:
                        setattr(self, k, v)

    def post_init(self):
        """
        Initialize class attributes/members that can/should not be (de)serialized in standard way.

        Examples:

            - deep learning models
            - index files
            - numpy arrays

        .. warning::
            All class members created here will NOT be serialized when calling :func:`save`. Therefore if you
            want to store them, please override the :func:`__getstate__`.
        """
        pass

    @classmethod
    def pre_init(cls):
        """This function is called before the object initiating (i.e. :func:`__call__`)

        Packages and environment variables can be set and load here.
        """
        pass

    @property
    def save_abspath(self) -> str:
        """Get the file path of the binary serialized object

        The file name ends with `.bin`.

        :return: the name of the file with `.bin`
        """
        return self.get_file_from_workspace(f'{self.name}.bin')

    @property
    def config_abspath(self) -> str:
        """Get the file path of the YAML config

        :return: The file name ends with `.yml`.
        """
        return self.get_file_from_workspace(f'{self.name}.yml')

    @staticmethod
    def get_shard_workspace(
        workspace_folder: str, workspace_name: str, pea_id: int
    ) -> str:
        """
        Get the path of the current shard.

        :param workspace_folder: Folder of the workspace.
        :param workspace_name: Name of the workspace.
        :param pea_id: Id of the pea,

        :return: returns the workspace of the shard of this Executor.
        """
        return os.path.join(workspace_folder, f'{workspace_name}-{pea_id}')

    @property
    def workspace_name(self):
        """Get the name of the workspace.

        :return: returns the name of the executor
        """
        return self.name

    @property
    def _workspace(self):
        """Property to access `workspace` if existing or default to `./`. Useful to provide good interface when
        using executors directly in python.

        .. highlight:: python
        .. code-block:: python

            with NumpyIndexer() as indexer:
                indexer.touch()

        :return: returns the workspace property of the executor or default to './'
        """
        return self.workspace or './'

    @property
    def shard_workspace(self) -> str:
        """Get the path of the current shard.

        :return: returns the workspace of the shard of this Executor
        """
        return BaseExecutor.get_shard_workspace(
            self._workspace, self.workspace_name, self.pea_id
        )

    def get_file_from_workspace(self, name: str) -> str:
        """Get a usable file path under the current workspace

        :param name: the name of the file

        :return: file path
        """
        Path(self.shard_workspace).mkdir(parents=True, exist_ok=True)
        return os.path.join(self.shard_workspace, name)

    @property
    def physical_size(self) -> int:
        """Return the size of the current workspace in bytes

        :return: byte size of the current workspace
        """
        root_directory = Path(self.shard_workspace)
        return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        for k in self._post_init_vars:
            del d[k]
        cached = [k for k in d.keys() if k.startswith('CACHED_')]
        for k in cached:
            del d[k]

        d.pop('_drivers', None)
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = JinaLogger(self.__class__.__name__)
        try:
            self._post_init_wrapper(fill_in_metas=False)
        except ModuleNotFoundError as ex:
            self.logger.warning(
                f'{typename(ex)} is often caused by a missing component, '
                f'which often can be solved by "pip install" relevant package: {ex!r}',
                exc_info=True,
            )

    def touch(self) -> None:
        """Touch the executor and change ``is_updated`` to ``True`` so that one can call :func:`save`. """
        self.is_updated = True

    def save(self, filename: str = None):
        """
        Persist data of this executor to the :attr:`shard_workspace`. The data could be
        a file or collection of files produced/used during an executor run.

        These are some of the common data that you might want to persist:

            - binary dump/pickle of the executor
            - the indexed files
            - (pre)trained models

        .. warning::
            All class members created here will NOT be serialized when calling :func:`save`. Therefore if you
            want to store them, please implement the :func:`__getstate__`.

        It uses ``pickle`` for dumping. For members/attributes that are not valid or not efficient for ``pickle``, you
        need to implement their own persistence strategy in the :func:`__getstate__`.

        :param filename: file path of the serialized file, if not given then :attr:`save_abspath` is used
        """
        if not self.read_only and self.is_updated:
            f = filename or self.save_abspath
            if not f:
                f = tempfile.NamedTemporaryFile(
                    'w', delete=False, dir=os.environ.get('JINA_EXECUTOR_WORKDIR', None)
                ).name

            if self.max_snapshot > 0 and os.path.exists(f):
                bak_f = (
                    f
                    + f'.snapshot-{self._last_snapshot_ts.strftime("%Y%m%d%H%M%S") or "NA"}'
                )
                os.rename(f, bak_f)
                self._snapshot_files.append(bak_f)
                if len(self._snapshot_files) > self.max_snapshot:
                    d_f = self._snapshot_files.pop(0)
                    if os.path.exists(d_f):
                        os.remove(d_f)
            with open(f, 'wb') as fp:
                pickle.dump(self, fp)
                self._last_snapshot_ts = datetime.now()
            self.is_updated = False
            self.logger.success(
                f'artifacts of this executor ({self.name}) is persisted to {f}'
            )
        else:
            if not self.is_updated:
                self.logger.info(
                    f'no update since {self._last_snapshot_ts:%Y-%m-%d %H:%M:%S%z}, will not save. '
                    'If you really want to save it, call "touch()" before "save()" to force saving'
                )

    @classmethod
    def inject_config(
        cls: Type[AnyExecutor],
        raw_config: Dict,
        pea_id: int = 0,
        read_only: bool = False,
        *args,
        **kwargs,
    ) -> Dict:
        """Inject config into the raw_config before loading into an object.

        :param raw_config: raw config to work on
        :param pea_id: the id of the storage of this parallel pea
        :param read_only: if the executor should be readonly
        :param args: Additional arguments.
        :param kwargs: Additional key word arguments.

        :return: an executor object
        """
        if 'metas' not in raw_config:
            raw_config['metas'] = {}
        tmp = fill_metas_with_defaults(raw_config)
        tmp['metas']['pea_id'] = pea_id
        tmp['metas']['read_only'] = read_only
        if kwargs.get('metas'):
            tmp['metas'].update(kwargs['metas'])
            del kwargs['metas']
        tmp.update(kwargs)
        return tmp

    @staticmethod
    def load(filename: str = None) -> AnyExecutor:
        """Build an executor from a binary file

        :param filename: the file path of the binary serialized file
        :return: an executor object

        It uses ``pickle`` for loading.
        """
        if not filename:
            raise FileNotFoundError
        try:
            with open(filename, 'rb') as fp:
                return pickle.load(fp)
        except EOFError:
            raise BadPersistantFile(f'broken file {filename} can not be loaded')

    def close(self) -> None:
        """
        Release the resources as executor is destroyed, need to be overridden
        """
        self.save()
        self.logger.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def attach(self, runtime: 'ZEDRuntime', *args, **kwargs):
        """Attach this executor to a Basepea

        This is called inside the initializing of a :class:`jina.peapods.runtime.BasePea`.

        :param runtime: Runtime procedure leveraging ZMQ.
        :param args: Additional arguments.
        :param kwargs: Additional key word arguments.
        """
        for drivers in self._drivers.values():
            for driver in drivers:
                driver.attach(executor=self, runtime=runtime, *args, **kwargs)

        # replacing the logger to runtime's logger
        if runtime and isinstance(getattr(runtime, 'logger', None), JinaLogger):
            self.logger = runtime.logger

    def __call__(self, req_type, *args, **kwargs):
        """


        # noqa: DAR201


        # noqa: DAR101


        # noqa: DAR102
        """
        if req_type in self._drivers:
            for d in self._drivers[req_type]:
                if d.attached:
                    d()
                else:
                    raise UnattachedDriver(d)
        else:
            raise NoDriverForRequest(f'{req_type} for {self}')

    def __str__(self):
        return self.__class__.__name__
