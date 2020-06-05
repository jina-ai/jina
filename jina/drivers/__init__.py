__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from functools import wraps
from typing import Callable, List

import ruamel.yaml.constructor

from ..executors.compound import CompoundExecutor
from ..helper import yaml
from ..proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    from ..peapods.pea import BasePea
    from ..executors import AnyExecutor
    import logging


def store_init_kwargs(func):
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError('this decorator should only be used on __init__ method of a driver')
        taboo = {'self', 'args', 'kwargs'}
        all_pars = inspect.signature(func).parameters
        tmp = {k: v.default for k, v in all_pars.items() if k not in taboo}
        tmp_list = [k for k in all_pars.keys() if k not in taboo]
        # set args by aligning tmp_list with arg values
        for k, v in zip(tmp_list, args):
            tmp[k] = v
        # set kwargs
        for k, v in kwargs.items():
            if k in tmp:
                tmp[k] = v

        if self.store_args_kwargs:
            if args: tmp['args'] = args
            if kwargs: tmp['kwargs'] = {k: v for k, v in kwargs.items() if k not in taboo}

        if hasattr(self, '_init_kwargs_dict'):
            self._init_kwargs_dict.update(tmp)
        else:
            self._init_kwargs_dict = tmp
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper


class DriverType(type):

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set:
            # print('reg class: %s' % cls.__name__)
            cls.__init__ = store_init_kwargs(cls.__init__)

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        yaml.register_class(cls)
        return cls


class BaseDriver(metaclass=DriverType):
    """A :class:`BaseDriver` is a logic unit above the :class:`jina.peapods.pea.BasePea`.
    It reads the protobuf message, extracts/modifies the required information and then return
    the message back to :class:`jina.peapods.pea.BasePea`.

    A :class:`BaseDriver` needs to be :attr:`attached` to a :class:`jina.peapods.pea.BasePea` before using. This is done by
    :func:`attach`. Note that a deserialized :class:`BaseDriver` from file is always unattached.
    """

    store_args_kwargs = False  #: set this to ``True`` to save ``args`` (in a list) and ``kwargs`` (in a map) in YAML config

    def __init__(self, *args, **kwargs):
        self.attached = False  #: represent if this driver is attached to a :class:`jina.peapods.pea.BasePea` (& :class:`jina.executors.BaseExecutor`)
        self.pea = None  # type: 'BasePea'

    def attach(self, pea: 'BasePea', *args, **kwargs):
        """Attach this driver to a :class:`jina.peapods.pea.BasePea`

        :param pea: the pea to be attached.
        """
        self.pea = pea
        self.attached = True

    @property
    def req(self) -> 'jina_pb2.Request':
        """Get the current request, shortcut to ``self.pea.request``"""
        return self.pea.request



    @property
    def msg(self) -> 'jina_pb2.Message':
        """Get the current request, shortcut to ``self.pea.message``"""
        return self.pea.message

    @property
    def envelope(self) -> 'jina_pb2.Envelope':
        """Get the current request, shortcut to ``self.pea.message``"""
        return self.pea.message.envelope

    @property
    def logger(self) -> 'logging.Logger':
        """Shortcut to ``self.pea.logger``"""
        return self.pea.logger

    def __call__(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @staticmethod
    def _dump_instance_to_yaml(data):
        # note: we only save non-default property for the sake of clarity
        a = {k: v for k, v in data._init_kwargs_dict.items()}
        r = {}
        if a:
            r['with'] = a
        return r

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        tmp = data._dump_instance_to_yaml(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls._get_instance_from_yaml(constructor, node)

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node):
        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True)

        obj = cls(**data.get('with', {}))
        return obj

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __getstate__(self):
        """Do not save the BasePea, as it would be cross-referencing. In other words, a deserialized :class:`BaseDriver` from
        file is always unattached. """
        d = dict(self.__dict__)
        if 'pea' in d:
            del d['pea']
        d['attached'] = False
        return d


class BaseExecutableDriver(BaseDriver):
    """A :class:`BaseExecutableDriver` is an intermediate logic unit between the :class:`jina.peapods.pea.BasePea` and :class:`jina.executors.BaseExecutor`
        It reads the protobuf message, extracts/modifies the required information and then sends to the :class:`jina.executors.BaseExecutor`,
        finally it returns the message back to :class:`jina.peapods.pea.BasePea`.

        A :class:`BaseExecutableDriver` needs to be :attr:`attached` to a :class:`jina.peapods.pea.BasePea` and :class:`jina.executors.BaseExecutor` before using.
        This is done by :func:`attach`. Note that a deserialized :class:`BaseDriver` from file is always unattached.
    """

    def __init__(self, executor: str = None, method: str = None, *args, **kwargs):
        """ Initialize a :class:`BaseExecutableDriver`

        :param executor: the name of the sub-executor, only necessary when :class:`jina.executors.compound.CompoundExecutor` is used
        :param method: the function name of the executor that the driver feeds to
        """
        super().__init__(*args, **kwargs)
        self._executor_name = executor
        self._method_name = method
        self._exec = None
        self._exec_fn = None

    @property
    def exec(self) -> 'AnyExecutor':
        """the executor that attached """
        return self._exec

    @property
    def exec_fn(self) -> Callable:
        """the function of :func:`jina.executors.BaseExecutor` to call """
        return self._exec_fn

    def attach(self, executor: 'AnyExecutor', *args, **kwargs):
        """Attach the driver to a :class:`jina.executors.BaseExecutor`"""
        super().attach(*args, **kwargs)
        if self._executor_name and isinstance(executor, CompoundExecutor):
            if self._executor_name in executor:
                self._exec = executor[self._executor_name]
            else:
                for c in executor.components:
                    if any(t.__name__ == self._executor_name for t in type.mro(c.__class__)):
                        self._exec = c
                        break
            if self._exec is None:
                self.logger.critical(f'fail to attach the driver to {executor}, '
                                     f'no executor is named or typed as {self._executor_name}')
        else:
            self._exec = executor

        if self._method_name:
            self._exec_fn = getattr(self.exec, self._method_name)

    def __getstate__(self):
        """Do not save the executor and executor function, as it would be cross-referencing and unserializable.
        In other words, a deserialized :class:`BaseExecutableDriver` from file is always unattached. """
        d = super().__getstate__()
        if '_exec' in d:
            del d['_exec']
        if '_exec_fn' in d:
            del d['_exec_fn']
        return d
