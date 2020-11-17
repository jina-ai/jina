__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import pickle
import re
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, Union, TypeVar, Type, TextIO, List

import ruamel.yaml.constructor
from ruamel.yaml import StringIO

from .decorators import as_train_method, as_update_method, store_init_kwargs, as_aggregate_method, wrap_func
from .metas import get_default_metas, fill_metas_with_defaults
from ..excepts import EmptyExecutorYAML, BadWorkspace, BadPersistantFile, NoDriverForRequest, UnattachedDriver
from ..helper import yaml, expand_dict, expand_env_var, get_local_config_source, typename
from ..importer import PathImporter
from ..logging import JinaLogger
from ..logging.profile import TimeContext

if False:
    from ..peapods.pea import BasePea
    from ..drivers import BaseDriver

__all__ = ['BaseExecutor', 'AnyExecutor', 'ExecutorType']

AnyExecutor = TypeVar('AnyExecutor', bound='BaseExecutor')

# some variables may be self-referred and they must be resolved at here
_ref_desolve_map = SimpleNamespace()
_ref_desolve_map.__dict__['metas'] = SimpleNamespace()
_ref_desolve_map.__dict__['metas'].__dict__['pea_id'] = 0
_ref_desolve_map.__dict__['metas'].__dict__['separated_workspace'] = False


class ExecutorType(type):

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    def __call__(cls, *args, **kwargs):
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
        update_funcs = ['train', 'add']
        train_funcs = ['train']
        aggregate_funcs = ['evaluate']

        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set or getattr(cls, 'force_register', False):

            wrap_func(cls, ['__init__'], store_init_kwargs)
            wrap_func(cls, train_funcs, as_train_method)
            wrap_func(cls, update_funcs, as_update_method)
            wrap_func(cls, aggregate_funcs, as_aggregate_method)

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        yaml.register_class(cls)
        return cls


class BaseExecutor(metaclass=ExecutorType):
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

    To use an executor in a :class:`jina.peapods.pea.BasePea` or :class:`jina.peapods.pod.BasePod`,
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
    exec_methods = ['encode', 'add', 'query', 'craft', 'score', 'evaluate', 'predict', 'query_by_id']

    def __init__(self, *args, **kwargs):
        if isinstance(args, tuple) and len(args) > 0:
            self.args = args[0]
        else:
            self.args = args
        self.logger = JinaLogger(self.__class__.__name__)
        self._snapshot_files = []
        self._post_init_vars = set()
        self._last_snapshot_ts = datetime.now()
        self._drivers = {}  # type: Dict[str, List['BaseDriver']]
        self._attached_pea = None

    def _check_on_gpu(self):
        if self.on_gpu:
            try:
                cuda_version = subprocess.check_output(['nvcc', '--version']).decode()
                self.logger.success(f'CUDA compiler version: {cuda_version}')
            except OSError:
                self.logger.warning(
                    'on_gpu=True, but you dont have CUDA compatible GPU, i will reset on_gpu=False ')
                self.on_gpu = False

    def _post_init_wrapper(self, _metas: Dict = None, _requests: Dict = None, fill_in_metas: bool = True) -> None:
        with TimeContext('post_init may take some time', self.logger):
            if fill_in_metas:
                if not _metas:
                    _metas = get_default_metas()

                if not _requests:
                    from ..executors.requests import get_default_reqs
                    _requests = get_default_reqs(type.mro(self.__class__))

                self._fill_metas(_metas)
                self._fill_requests(_requests)

            self._check_on_gpu()
            _before = set(list(vars(self).keys()))
            self.post_init()
            self._post_init_vars = {k for k in vars(self) if k not in _before}

    def _fill_requests(self, _requests):

        if _requests and 'on' in _requests and isinstance(_requests['on'], dict):
            # if control request is forget in YAML, then fill it
            if 'ControlRequest' not in _requests['on']:
                from ..drivers.control import ControlReqDriver
                _requests['on']['ControlRequest'] = [ControlReqDriver()]

            for req_type, drivers in _requests['on'].items():
                if isinstance(req_type, str):
                    req_type = [req_type]
                for r in req_type:
                    if r not in self._drivers:
                        self._drivers[r] = list()
                    if self._drivers[r] != drivers:
                        self._drivers[r].extend(drivers)

    def _fill_metas(self, _metas):
        unresolved_attr = False
        # set self values filtered by those non-exist, and non-expandable
        for k, v in _metas.items():
            if not hasattr(self, k):
                if isinstance(v, str):
                    if not (re.match(r'{.*?}', v) or re.match(r'\$.*\b', v)):
                        setattr(self, k, v)
                    else:
                        unresolved_attr = True
                else:
                    setattr(self, k, v)
            elif type(getattr(self, k)) == type(v):
                setattr(self, k, v)
        if not getattr(self, 'name', None):
            _id = str(uuid.uuid4()).split('-')[0]
            _name = f'{typename(self)}-{_id}'
            if self.warn_unnamed:
                self.logger.warning(
                    f'this executor is not named, i will call it "{_name}". '
                    'naming is important as it provides an unique identifier when '
                    'persisting this executor on disk.')
            setattr(self, 'name', _name)
        if unresolved_attr:
            _tmp = vars(self)
            _tmp['metas'] = _metas
            new_metas = expand_dict(_tmp)['metas']

            # set self values filtered by those non-exist, and non-expandable
            for k, v in new_metas.items():
                if not hasattr(self, k):
                    if isinstance(v, str) and (re.match(r'{.*?}', v) or re.match(r'\$.*\b', v)):
                        v = expand_env_var(v.format(root=_ref_desolve_map, this=_ref_desolve_map))
                    if isinstance(v, str):
                        if not (re.match(r'{.*?}', v) or re.match(r'\$.*\b', v)):
                            setattr(self, k, v)
                        else:
                            raise ValueError(f'{k}={v} is not expandable or badly referred')
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
        """
        return self.get_file_from_workspace(f'{self.name}.bin')

    @property
    def config_abspath(self) -> str:
        """Get the file path of the YAML config

        The file name ends with `.yml`.
        """
        return self.get_file_from_workspace(f'{self.name}.yml')

    @property
    def current_workspace(self) -> str:
        """ Get the path of the current workspace.

        :return: if ``separated_workspace`` is set to ``False`` then ``metas.workspace`` is returned,
                otherwise the ``metas.pea_workspace`` is returned
        """
        work_dir = self.pea_workspace if self.separated_workspace else self.workspace  # type: str
        return work_dir

    def get_file_from_workspace(self, name: str) -> str:
        """Get a usable file path under the current workspace

        :param name: the name of the file

        :return depending on ``metas.separated_workspace`` the file could be located in ``metas.workspace`` or ``metas.pea_workspace``
        """
        Path(self.current_workspace).mkdir(parents=True, exist_ok=True)
        return os.path.join(self.current_workspace, name)

    @property
    def physical_size(self) -> int:
        """Return the size of the current workspace in bytes"""
        root_directory = Path(self.current_workspace)
        return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        for k in self._post_init_vars:
            del d[k]
        cached = [k for k in d.keys() if k.startswith('CACHED_')]
        for k in cached:
            del d[k]
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = JinaLogger(self.__class__.__name__)
        try:
            self._post_init_wrapper(fill_in_metas=False)
        except ModuleNotFoundError as ex:
            self.logger.warning(f'{typename(ex)} is often caused by a missing component, '
                                f'which often can be solved by "pip install" relevant package: {repr(ex)}',
                                exc_info=True)

    def train(self, *args, **kwargs) -> None:
        """
        Train this executor, need to be overrided
        """
        pass

    def touch(self) -> None:
        """Touch the executor and change ``is_updated`` to ``True`` so that one can call :func:`save`. """
        self.is_updated = True

    def save(self, filename: str = None) -> bool:
        """
        Persist data of this executor to the :attr:`workspace` (or :attr:`pea_workspace`). The data could be
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
        :return: successfully persisted or not
        """
        if not self.is_updated:
            self.logger.info(f'no update since {self._last_snapshot_ts:%Y-%m-%d %H:%M:%S%z}, will not save. '
                             'If you really want to save it, call "touch()" before "save()" to force saving')
            return False

        self.is_updated = False
        f = filename or self.save_abspath
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('JINA_EXECUTOR_WORKDIR', None)).name

        if self.max_snapshot > 0 and os.path.exists(f):
            bak_f = f + f'.snapshot-{self._last_snapshot_ts.strftime("%Y%m%d%H%M%S") or "NA"}'
            os.rename(f, bak_f)
            self._snapshot_files.append(bak_f)
            if len(self._snapshot_files) > self.max_snapshot:
                d_f = self._snapshot_files.pop(0)
                if os.path.exists(d_f):
                    os.remove(d_f)

        with open(f, 'wb') as fp:
            pickle.dump(self, fp)
            self._last_snapshot_ts = datetime.now()

        self.logger.success(f'artifacts of this executor ({self.name}) is persisted to {f}')
        return True

    def save_config(self, filename: str = None) -> bool:
        """
        Serialize the object to a yaml file

        :param filename: file path of the yaml file, if not given then :attr:`config_abspath` is used
        :return: successfully dumped or not
        """
        _updated, self.is_updated = self.is_updated, False
        f = filename or self.config_abspath
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('JINA_EXECUTOR_WORKDIR', None)).name
        with open(f, 'w', encoding='utf8') as fp:
            yaml.dump(self, fp)
        self.logger.info(f'executor\'s yaml config is save to {f}')

        self.is_updated = _updated
        return True

    @classmethod
    def load_config(cls: Type[AnyExecutor], source: Union[str, TextIO], separated_workspace: bool = False,
                    pea_id: int = 0) -> AnyExecutor:
        """Build an executor from a YAML file.

        :param filename: the file path of the YAML file or a ``TextIO`` stream to be loaded from
        :param separated_workspace: the dump and data files associated to this executor will be stored separately for
                each parallel pea, which will be indexed by the ``pea_id``
        :param pea_id: the id of the storage of this parallel pea, only effective when ``separated_workspace=True``
        :return: an executor object
        """
        if not source: raise FileNotFoundError
        source = get_local_config_source(source)
        # first scan, find if external modules are specified
        with (open(source, encoding='utf8') if isinstance(source, str) else source) as fp:
            # ignore all lines start with ! because they could trigger the deserialization of that class
            safe_yml = '\n'.join(v if not re.match(r'^[\s-]*?!\b', v) else v.replace('!', '__tag: ') for v in fp)
            tmp = yaml.load(safe_yml)
            if tmp:
                if 'metas' not in tmp:
                    tmp['metas'] = {}
                tmp = fill_metas_with_defaults(tmp)

                if 'py_modules' in tmp['metas'] and tmp['metas']['py_modules']:
                    mod = tmp['metas']['py_modules']

                    if isinstance(mod, str):
                        mod = [mod]

                    if isinstance(mod, list):
                        mod = [m if os.path.isabs(m) else os.path.join(os.path.dirname(source), m) for m in mod]
                        PathImporter.add_modules(*mod)
                    else:
                        raise TypeError(f'{type(mod)!r} is not acceptable, only str or list are acceptable')

                tmp['metas']['separated_workspace'] = separated_workspace
                tmp['metas']['pea_id'] = pea_id

            else:
                raise EmptyExecutorYAML(f'{source} is empty? nothing to read from there')

            tmp = expand_dict(tmp)
            stream = StringIO()
            yaml.dump(tmp, stream)
            tmp_s = stream.getvalue().strip().replace('__tag: ', '!')
            return yaml.load(tmp_s)

    @staticmethod
    def load(filename: str = None) -> AnyExecutor:
        """Build an executor from a binary file

        :param filename: the file path of the binary serialized file
        :return: an executor object

        It uses ``pickle`` for loading.
        """
        if not filename: raise FileNotFoundError
        try:
            with open(filename, 'rb') as fp:
                return pickle.load(fp)
        except EOFError:
            raise BadPersistantFile(f'broken file {filename} can not be loaded')

    def close(self) -> None:
        """
        Release the resources as executor is destroyed, need to be overrided
        """
        self.logger.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        tmp = data._dump_instance_to_yaml(data)
        if getattr(data, '_drivers'):
            tmp['requests'] = {'on': data._drivers}
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls._get_instance_from_yaml(constructor, node)[0]

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node):
        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True)

        _meta_config = get_default_metas()
        _meta_config.update(data.get('metas', {}))
        if _meta_config:
            data['metas'] = _meta_config

        dump_path = cls._get_dump_path_from_config(data.get('metas', {}))
        load_from_dump = False
        if dump_path:
            obj = cls.load(dump_path)
            obj.logger.success(f'restore {cls.__name__} from {dump_path}')
            load_from_dump = True
        else:
            cls.init_from_yaml = True

            if cls.store_args_kwargs:
                p = data.get('with', {})  # type: Dict[str, Any]
                a = p.pop('args') if 'args' in p else ()
                k = p.pop('kwargs') if 'kwargs' in p else {}
                # maybe there are some hanging kwargs in "parameters"
                # tmp_a = (expand_env_var(v) for v in a)
                # tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
                tmp_a = a
                tmp_p = {kk: vv for kk, vv in {**k, **p}.items()}
                obj = cls(*tmp_a, **tmp_p, metas=data.get('metas', {}), requests=data.get('requests', {}))
            else:
                # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}
                obj = cls(**data.get('with', {}), metas=data.get('metas', {}), requests=data.get('requests', {}))

            obj.logger.success(f'successfully built {cls.__name__} from a yaml config')
            cls.init_from_yaml = False

        # if node.tag in {'!CompoundExecutor'}:
        #     os.environ['JINA_WARN_UNNAMED'] = 'YES'

        if not _meta_config:
            obj.logger.warning(
                '"metas" config is not found in this yaml file, '
                'this map is important as it provides an unique identifier when '
                'persisting the executor on disk.')

        return obj, data, load_from_dump

    @staticmethod
    def _get_dump_path_from_config(meta_config: Dict):
        if 'name' in meta_config:
            if meta_config.get('separated_workspace', False) is True:
                if 'pea_id' in meta_config and isinstance(meta_config['pea_id'], int):
                    work_dir = meta_config['pea_workspace']
                    dump_path = os.path.join(work_dir, f'{meta_config["name"]}.{"bin"}')
                    if os.path.exists(dump_path):
                        return dump_path
                else:
                    raise BadWorkspace('separated_workspace=True but pea_id is unset or set to a bad value')
            else:
                dump_path = os.path.join(meta_config.get('workspace', os.getcwd()),
                                         f'{meta_config["name"]}.{"bin"}')
                if os.path.exists(dump_path):
                    return dump_path

    @staticmethod
    def _dump_instance_to_yaml(data) -> Dict[str, Dict]:
        # note: we only save non-default property for the sake of clarity
        _defaults = get_default_metas()
        p = {k: getattr(data, k) for k, v in _defaults.items() if getattr(data, k) != v}
        a = {k: v for k, v in data._init_kwargs_dict.items() if k not in _defaults}
        r = {}
        if a:
            r['with'] = a
        if p:
            r['metas'] = p
        return r

    def attach(self, pea: 'BasePea', *args, **kwargs):
        """Attach this executor to a :class:`jina.peapods.pea.BasePea`.

        This is called inside the initializing of a :class:`jina.peapods.pea.BasePea`.
        """
        for v in self._drivers.values():
            for d in v:
                d.attach(executor=self, pea=pea, *args, **kwargs)

        # replacing the logger to pea's logger
        if pea and isinstance(getattr(pea, 'logger', None), JinaLogger):
            self.logger = pea.logger

    def __call__(self, req_type, *args, **kwargs):
        if req_type in self._drivers:
            for d in self._drivers[req_type]:
                if d.attached:
                    d()
                else:
                    raise UnattachedDriver(d)
        else:
            raise NoDriverForRequest(req_type)

    def __str__(self):
        return self.__class__.__name__
