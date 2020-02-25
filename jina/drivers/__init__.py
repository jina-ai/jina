from typing import Callable, List

import ruamel.yaml.constructor

from ..executors.compound import CompoundExecutor
from ..executors.decorators import store_init_kwargs
from ..helper import yaml
from ..proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    from ..peapods.pea import Pea
    from ..executors import AnyExecutor
    import logging


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
    store_args_kwargs = False  #: set this to ``True`` to save ``args`` (in a list) and ``kwargs`` (in a map) in YAML config

    def __init__(self, *args, **kwargs):
        pass

    def attach(self, pea: 'Pea', *args, **kwargs):
        self.pea = pea

    @property
    def req(self) -> 'jina_pb2.Request':
        """Get the current request, shortcut to ``self.pea.request``"""
        return self.pea.request

    @property
    def prev_reqs(self) -> List['jina_pb2.Request']:
        """Get all previous requests that has the same ``request_id``, shortcut to ``self.pea.prev_requests``

        This returns ``None`` when ``num_part=1``.
        """
        return self.pea.prev_requests

    @property
    def msg(self) -> 'jina_pb2.Message':
        """Get the current request, shortcut to ``self.pea.message``"""
        return self.pea.message

    @property
    def prev_msgs(self) -> List['jina_pb2.Message']:
        """Get all previous messages that has the same ``request_id``, shortcut to ``self.pea.prev_messages``

        This returns ``None`` when ``num_part=1``.
        """
        return self.pea.prev_messages

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
        """Do not save the Pea, as it would be cross-referencing. In other words, a deserialized :class:`BaseDriver` from
        file is always unattached. """
        d = dict(self.__dict__)
        if 'pea' in d:
            del d['pea']
        return d


class BaseExecutorDriver(BaseDriver):

    def __init__(self, executor: str = None, method: str = None, *args, **kwargs):
        """ Initialize a driver

        :param executor:
        :param method:
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._executor_name = executor
        self._method_name = method

    @property
    def exec(self) -> 'AnyExecutor':
        """the executor that attached """
        return self._exec

    @property
    def exec_fn(self) -> Callable:
        """the function of :func:`jina.executors.BaseExecutor` to call """
        return self._exec_fn

    def attach(self, executor: 'AnyExecutor', *args, **kwargs):
        super().attach(*args, **kwargs)
        if self._executor_name and isinstance(executor, CompoundExecutor):
            self._exec = executor.components[self._executor_name]
        else:
            self._exec = executor

        if self._method_name:
            self._exec_fn = getattr(self.exec, self._method_name)

    def __getstate__(self):
        """Do not save the executor and executor function, as it would be cross-referencing and unserializable.
        In other words, a deserialized :class:`BaseExecutorDriver` from file is always unattached. """
        d = dict(self.__dict__)
        if '_exec' in d:
            del d['_exec']
        if '_exec_fn' in d:
            del d['_exec_fn']
        return d
