import os
import pickle
import sys
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, Union, TypeVar, Type, List, TextIO

import ruamel.yaml.constructor

from .decorators import as_train_method, as_update_method, store_init_kwargs
from .metas import defaults
from ..helper import yaml, print_load_table, PathImporter, expand_env_var
from ..logging.base import get_logger
from ..logging.profile import profiling

__all__ = ['BaseExecutor', 'AnyExecutor', 'import_executors']

AnyExecutor = TypeVar('AnyExecutor', bound='BaseExecutor')


class ExecutorType(type):

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    def __call__(cls, *args, **kwargs):
        # do _preload_package
        getattr(cls, 'pre_init', lambda *x: None)()

        if 'metas' in kwargs:
            jina_config = kwargs.pop('metas')
        else:
            jina_config = {}

        obj = type.__call__(cls, *args, **kwargs)

        # set attribute with priority
        # metas in YAML > class attribute > default_jina_config
        for k, v in defaults.items():
            if k in jina_config:
                v = jina_config[k]
            v = expand_env_var(v)
            if not hasattr(obj, k):
                setattr(obj, k, v)

        getattr(obj, '_post_init_wrapper', lambda *x: None)()
        return obj

    @staticmethod
    def register_class(cls):
        prof_funcs = ['train', 'encode', 'add', 'query', 'transform', 'score']
        update_funcs = ['train', 'add']
        train_funcs = ['train']

        def wrap_func(func_lst, wrapper):
            for f_name in func_lst:
                if hasattr(cls, f_name):
                    setattr(cls, f_name, wrapper(getattr(cls, f_name)))

        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set:
            # print('reg class: %s' % cls.__name__)
            cls.__init__ = store_init_kwargs(cls.__init__)
            if os.environ.get('JINA_PROFILING', False):
                wrap_func(prof_funcs, profiling)

            wrap_func(train_funcs, as_train_method)
            wrap_func(update_funcs, as_update_method)

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

    To use an executor in a :class:`jina.peapods.pea.Pea` or :class:`jina.peapods.pod.Pod`,
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

    def __init__(self, *args, **kwargs):
        self.logger = get_logger(self.__class__.__name__)
        self._snapshot_files = []
        self._post_init_vars = set()
        self._last_snapshot_ts = datetime.now()

    def _post_init_wrapper(self):
        if not getattr(self, 'name', None):
            _id = str(uuid.uuid4()).split('-')[0]
            _name = '%s-%s' % (self.__class__.__name__, _id)
            if self.warn_unnamed:
                self.logger.warning(
                    'this executor is not named, i will call it "%s". '
                    'naming is important as it provides an unique identifier when '
                    'persisting this executor on disk.' % _name)
            setattr(self, 'name', _name)

        _before = set(list(self.__dict__.keys()))
        self.post_init()
        self._post_init_vars = {k for k in self.__dict__ if k not in _before}

    def post_init(self):
        """
        Initialize class attributes/members that can/should not be (de)serialized in standard way.

        Examples:

            - deep learning models
            - index files
            - numpy arrays

        .. note::
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
        return os.path.join(self.work_dir, '%s.bin' % self.name)

    @property
    def config_abspath(self) -> str:
        """Get the file path of the YAML config

        The file name ends with `.yml`.
        """
        return os.path.join(self.work_dir, '%s.yml' % self.name)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        for k in self._post_init_vars:
            del d[k]
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = get_logger(self.__class__.__name__)
        try:
            self._post_init_wrapper()
        except ImportError as ex:
            self.logger.warning('ImportError is often caused by a missing component, '
                                'which often can be solved by "pip install" relevant package. %s' % ex, exc_info=True)

    def train(self, *args, **kwargs):
        """
        Train this executor, need to be overrided
        """
        pass

    def touch(self):
        """Touch the executor and change ``is_updated`` to ``True`` so that one can call :func:`save`. """
        self.is_updated = True

    @profiling
    def save(self, filename: str = None) -> bool:
        """
        Serialize the object to a binary file

        :param filename: file path of the serialized file, if not given then :attr:`save_abspath` is used
        :return: successfully dumped or not

        It uses ``pickle`` for dumping.

        """
        if not self.is_updated:
            self.logger.info('no update since %s, will not save. '
                             'If you really want to save it, call "touch()" before "save()" to force saving'
                             % self._last_snapshot_ts)
            return False

        self.is_updated = False
        f = filename or self.save_abspath
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('JINA_EXECUTOR_WORKDIR', None)).name

        if self.max_snapshot > 0 and os.path.exists(f):
            bak_f = f + '.snapshot-%s' % (self._last_snapshot_ts.strftime('%Y%m%d%H%M%S') or 'NA')
            os.rename(f, bak_f)
            self._snapshot_files.append(bak_f)
            if len(self._snapshot_files) > self.max_snapshot:
                d_f = self._snapshot_files.pop(0)
                if os.path.exists(d_f):
                    os.remove(d_f)

        with open(f, 'wb') as fp:
            pickle.dump(self, fp)
            self._last_snapshot_ts = datetime.now()

        self.logger.critical('this executor (%s) is serialized to %s' % (self.name, f))
        return True

    @profiling
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
        self.logger.info('executor\'s yaml config is save to %s' % f)

        self.is_updated = _updated
        return True

    @classmethod
    def load_config(cls: Type[AnyExecutor], filename: Union[str, TextIO]) -> AnyExecutor:
        """Build an executor from a YAML file.

        :param filename: the file path of the YAML file or a ``TextIO`` stream to be loaded from
        :return: an executor object
        """
        if not filename: raise FileNotFoundError
        import_executors(show_import_table=False, import_once=True)
        if isinstance(filename, str):
            # first scan, find if external modules are specified
            with open(filename, encoding='utf8') as fp:
                # the first line should always starts with !ClassName
                fp.readline()
                tmp = yaml.load(fp)
                if tmp and 'metas' in tmp and 'py_modules' in tmp['metas'] and tmp['metas']['py_modules']:
                    mod = tmp['metas']['py_modules']

                    if isinstance(mod, str):
                        if not os.path.isabs(mod):
                            mod = os.path.join(os.path.dirname(filename), mod)
                        PathImporter.add_modules(mod)
                    elif isinstance(mod, list):
                        mod = [m if os.path.isabs(m) else os.path.join(os.path.dirname(filename), m) for m in mod]
                        PathImporter.add_modules(*mod)
                    else:
                        raise TypeError('%r is not acceptable, only str or list are acceptable' % type(mod))

            # second scan, deserialize from the yaml
            with open(filename, encoding='utf8') as fp:
                return yaml.load(fp)
        else:
            with filename:
                return yaml.load(filename)

    @staticmethod
    @profiling
    def load(filename: str = None) -> AnyExecutor:
        """Build an executor from a binary file

        :param filename: the file path of the binary serialized file
        :return: an executor object

        It uses ``pickle`` for loading.
        """
        if not filename: raise FileNotFoundError
        with open(filename, 'rb') as fp:
            return pickle.load(fp)

    def close(self):
        """
        Release the resources as executor is destroyed, need to be overrided
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _get_tags_from_node(node):
        def node_recurse_generator(n):
            if n.tag.startswith('!'):
                yield n.tag.lstrip('!')
            for nn in n.value:
                if isinstance(nn, tuple):
                    for k in nn:
                        yield from node_recurse_generator(k)
                elif isinstance(nn, ruamel.yaml.nodes.Node):
                    yield from node_recurse_generator(nn)

        return list(set(list(node_recurse_generator(node))))

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        tmp = data._dump_instance_to_yaml(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node, stop_on_import_error=False):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls._get_instance_from_yaml(constructor, node, stop_on_import_error)[0]

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node, stop_on_import_error=False):
        try:
            import_executors(execs=cls._get_tags_from_node(node))
        except ImportError as ex:
            if stop_on_import_error:
                raise RuntimeError('Cannot import module, pip install may required') from ex

        # if node.tag in {'!PipelineEncoder', '!CompoundExecutor'}:
        #     os.unsetenv('JINA_WARN_UNNAMED')

        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True)

        _jina_config = data.get('metas', {})
        for k, v in _jina_config.items():
            _jina_config[k] = expand_env_var(v)
        if _jina_config:
            data['metas'] = _jina_config

        dump_path = cls._get_dump_path_from_config(data.get('metas', {}))
        load_from_dump = False
        if dump_path:
            obj = cls.load(dump_path)
            obj.logger.critical('restore %s from %s' % (cls.__name__, dump_path))
            load_from_dump = True
        else:
            cls.init_from_yaml = True

            if cls.store_args_kwargs:
                p = data.get('with', {})  # type: Dict[str, Any]
                a = p.pop('args') if 'args' in p else ()
                k = p.pop('kwargs') if 'kwargs' in p else {}
                # maybe there are some hanging kwargs in "parameters"
                tmp_a = (expand_env_var(v) for v in a)
                tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
                obj = cls(*tmp_a, **tmp_p, metas=data.get('metas', {}))
            else:
                tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}
                obj = cls(**tmp_p, metas=data.get('metas', {}))

            obj.logger.critical('initialize %s from a yaml config' % cls.__name__)
            cls.init_from_yaml = False

        # if node.tag in {'!CompoundExecutor'}:
        #     os.environ['JINA_WARN_UNNAMED'] = 'YES'

        if not _jina_config:
            obj.logger.warning(
                '"metas" config is not found in this yaml file, '
                'this map is important as it provides an unique identifier when '
                'persisting the executor on disk.')

        return obj, data, load_from_dump

    @staticmethod
    def _get_dump_path_from_config(jina_config: Dict):
        if 'name' in jina_config:
            dump_path = os.path.join(jina_config.get('work_dir', os.getcwd()), '%s.bin' % jina_config['name'])
            if os.path.exists(dump_path):
                return dump_path

    @staticmethod
    def _dump_instance_to_yaml(data):
        # note: we only save non-default property for the sake of clarity
        p = {k: getattr(data, k) for k, v in defaults.items() if getattr(data, k) != v}
        a = {k: v for k, v in data._init_kwargs_dict.items() if k not in defaults}
        r = {}
        if a:
            r['with'] = a
        if p:
            r['metas'] = p
        return r


def import_executors(path: str = __path__[0], namespace: str = 'jina.executors', execs: Union[str, List[str]] = None,
                     show_import_table: bool = False, import_once: bool = False):
    """
    Import all or selected executors into the runtime. This is used during :func:`load_config` to register the YAML
    constructor beforehand. It can be also used to import third-part or external executors.

    :param path: the package path for search
    :param namespace: the namespace to add given the ``path``
    :param execs: the list of executor names to import
    :param show_import_table: show the import result as a table
    :param import_once: import everything only once, to avoid repeated import
    """

    from .. import JINA_GLOBAL
    if import_once and JINA_GLOBAL.executors_imported:
        return

    from setuptools import find_packages
    from pkgutil import iter_modules

    modules = set()

    for info in iter_modules([path]):
        if not info.ispkg:
            modules.add('.'.join([namespace, info.name]))

    for pkg in find_packages(path):
        modules.add('.'.join([namespace, pkg]))
        pkgpath = path + '/' + pkg.replace('.', '/')
        if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
            for _, name, ispkg in iter_modules([pkgpath]):
                if not ispkg:
                    modules.add('.'.join([namespace, pkg, name]))
        else:
            for info in iter_modules([pkgpath]):
                if not info.ispkg:
                    modules.add('.'.join([namespace, pkg, info.name]))

    load_stat = defaultdict(list)
    bad_imports = []

    if isinstance(execs, str):
        execs = {execs}
    elif isinstance(execs, list):
        execs = set(execs)
    elif execs is None:
        execs = {}
    else:
        raise TypeError('target_exes must be a set, but received %r' % execs)

    import importlib
    for m in modules:
        try:
            mod = importlib.import_module(m)
            for k in dir(mod):
                # import the class
                if isinstance(getattr(mod, k), ExecutorType) and (not execs or k in execs):
                    try:
                        getattr(mod, k)
                        load_stat[m].append((k, True, ''))
                        if k in execs:
                            execs.remove(k)
                            if not execs:
                                return  # target execs are all found and loaded, return
                    except Exception as ex:
                        load_stat[m].append((k, False, ex))
                        bad_imports.append('.'.join([m, k]))
                        if k in execs:
                            raise ex  # target class is found but not loaded, raise return
        except Exception as ex:
            load_stat[m].append(('', False, ex))
            bad_imports.append(m)

    if execs:
        raise ImportError('%s can not be found in jina' % execs)

    if show_import_table:
        print_load_table(load_stat)
    else:
        if bad_imports:
            from jina.logging import default_logger
            default_logger.error('theses modules or classes can not be imported %s' % bad_imports)

    JINA_GLOBAL.executors_imported = True
