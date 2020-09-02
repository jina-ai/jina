__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from functools import wraps
from typing import Any, Dict, Callable, Tuple, Iterable, Iterator

import ruamel.yaml.constructor

from ..enums import OnErrorSkip
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


class QuerySetReader:
    """
    :class:`QuerySetReader` allows a driver to read arguments from the protobuf message. This allows a
    driver to override its behavior based on the message it receives. Extremely useful in production, for example,
    get ``top_k`` results, doing pagination, filtering.

    To register the field you want to read from the message, simply register them in :meth:`__init__`.
    For example, ``__init__(self, arg1, arg2, **kwargs)`` will allow the driver to read field ``arg1`` and ``arg2`` from
    the message. When they are not found in the message, the value ``_arg1`` and ``_arg2`` will be used. Note the underscore
    prefix.

    .. note::
        - To set default value of ``arg1``, use ``self._arg1 = ``, note the underscore in the front.
        - To access ``arg1``, simply use ``self.arg1``. It automatically switch between default ``_arg1`` and ``arg1`` from the request.

    For successful value reading, the following condition must be met:

        - the ``name`` in the proto must match with the current class name
        - the ``disabled`` field in the proto should not be ``False``
        - the ``priority`` in the proto should be strictly greater than the driver's priority (by default is 0)
        - the field name must exist in proto's ``parameters``

    """

    def _get_parameter(self, key: str, default: Any):
        if getattr(self, 'queryset', None):
            for q in self.queryset:
                if (not q.disabled and self.__class__.__name__ == q.name and
                        q.priority > self._priority and key in q.parameters):
                    return q.parameters[key]
        return getattr(self, f'_{key}', default)

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if name == '_init_kwargs_dict':
            # raise attribute error to avoid recursive call
            raise AttributeError
        if name in self._init_kwargs_dict:
            return self._get_parameter(name, default=self._init_kwargs_dict[name])
        raise AttributeError


class DriverType(type):

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set or getattr(cls, 'force_register', False):
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

    def __init__(self, priority: int = 0, *args, **kwargs):
        """

        :param priority: the priority of its default arg values (hardcoded in Python). If the
             received ``QueryLang`` has a higher priority, it will override the hardcoded value
        """
        self.attached = False  #: represent if this driver is attached to a :class:`jina.peapods.pea.BasePea` (& :class:`jina.executors.BaseExecutor`)
        self.pea = None  # type: 'BasePea'
        self._priority = priority

    def attach(self, pea: 'BasePea', *args, **kwargs) -> None:
        """Attach this driver to a :class:`jina.peapods.pea.BasePea`

        :param pea: the pea to be attached.
        """
        self.pea = pea
        self.attached = True

    @property
    def req(self) -> 'jina_pb2.Request':
        """Get the current (typed) request, shortcut to ``self.pea.request``"""
        return self.pea.request

    @property
    def msg(self) -> 'jina_pb2.Message':
        """Get the current request, shortcut to ``self.pea.message``"""
        return self.pea.message

    @property
    def queryset(self) -> Iterator['jina_pb2.QueryLang']:
        if self.msg:
            return self.msg.request.queryset
        else:
            return []

    @property
    def envelope(self) -> 'jina_pb2.Envelope':
        """Get the current request, shortcut to ``self.pea.message``"""
        return self.msg.envelope

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

    def __getstate__(self) -> Dict[str, Any]:
        """Do not save the BasePea, as it would be cross-referencing. In other words, a deserialized :class:`BaseDriver` from
        file is always unattached. """
        d = dict(self.__dict__)
        if 'pea' in d:
            del d['pea']
        d['attached'] = False
        return d


class BaseRecursiveDriver(BaseDriver):

    def __init__(self, recur_range: Tuple[int] = (0, 1), apply_order: str = 'post',
                 recur_on: Tuple[str] = ('chunks',), *args, **kwargs):
        """

        :param recur_range: right-exclusive range of the recursion depth, (0, 1) for root-level only
        :param apply_order: the traverse and apply order. if 'post' then first traverse then call apply, if 'pre' then first apply then traverse
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._depth_start = recur_range[0]
        self._depth_end = recur_range[1]
        if isinstance(recur_on, str):
            recur_on = (recur_on,)
        self.traverse_fields = set(recur_on)
        if apply_order in {'post', 'pre'}:
            self.recursion_order = apply_order
        else:
            raise AttributeError('can only accept oder={"pre", "post"}')
        self._is_apply = True
        self._is_apply_all = True

    def _apply(self, doc: 'jina_pb2.Document', context_doc: 'jina_pb2.Document', field: str, *args, **kwargs):
        """ Apply function works on each doc, one by one, modify the doc in-place

        :param doc: the :class:`jina_pb2.Document` object to work on. It could come from ``matches``/``chunks``.
        :param context_doc: the owner of ``doc``
        :param field: where ``doc`` comes from, either ``matches`` or ``chunks``
        """

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], context_doc: 'jina_pb2.Document', field: str, *args,
                   **kwargs):
        """ Apply function works on a list of docs, modify the docs in-place

        Depending on the value of ``order`` of :class:`BaseRecursiveDriver`, :meth:`apply_all` applies before or after :meth:`apply`

        :param docs: a list of :class:`jina_pb2.Document` objects to work on; they could come from ``matches``/``chunks``.
        :param context_doc: the owner of ``docs``
        :param field: where ``docs`` comes from, either ``matches`` or ``chunks``
        """

    def __call__(self, *args, **kwargs):
        self._traverse_apply(self.req.docs, *args, **kwargs)

    def _traverse_apply(self, docs, *args, **kwargs):
        """often useful when you delete a recursive structure """

        def post_traverse(_docs, recur_on, context_doc=None):
            """
            :param _docs: list of docs
            :param recur_on: "matches" or "chunks"
            :param context_doc: the owner of ``_docs``, if None, then it is at the very top-level
            :return:
            """
            if _docs:
                for d in _docs:
                    # check if apply to next level
                    if getattr(d, depth_name) < self._depth_end:
                        post_traverse(getattr(d, recur_on), recur_on, d)
                    # check if apply to the current level
                    if self._is_apply and self._depth_start <= getattr(d, depth_name) < self._depth_end:
                        self._apply(d, context_doc, recur_on, *args, **kwargs)

                # check first doc if in the required depth range
                if self._is_apply_all and getattr(_docs[0], depth_name) >= self._depth_start:
                    self._apply_all(_docs, context_doc, recur_on, *args, **kwargs)

        def pre_traverse(_docs, recur_on, context_doc=None):
            if _docs:
                # check first doc if in the required depth range
                if self._is_apply_all and getattr(_docs[0], depth_name) >= self._depth_start:
                    self._apply_all(_docs, context_doc, recur_on, *args, **kwargs)

                for d in _docs:
                    # check if apply on the current level
                    if self._is_apply and self._depth_start <= getattr(d, depth_name) < self._depth_end:
                        self._apply(d, context_doc, recur_on, *args, **kwargs)
                    # check if apply to the next level
                    if getattr(d, depth_name) < self._depth_end:
                        pre_traverse(getattr(d, recur_on), recur_on, d)

        if self.recursion_order == 'post':
            _traverse = post_traverse
        elif self.recursion_order == 'pre':
            _traverse = pre_traverse
        else:
            raise ValueError(f'{self.recursion_order}')

        if 'chunks' in self.traverse_fields:
            depth_name = 'granularity'
            _traverse(docs, 'chunks')

        if 'matches' in self.traverse_fields:
            depth_name = 'adjacency'
            for d in docs:
                _traverse(d.matches, 'matches')


class BaseExecutableDriver(BaseRecursiveDriver):
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
        if self.envelope.status.code != jina_pb2.Status.ERROR or self.pea.args.skip_on_error < OnErrorSkip.EXECUTOR:
            return self._exec_fn
        else:
            return lambda *args, **kwargs: None

    def attach(self, executor: 'AnyExecutor', *args, **kwargs) -> None:
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

    def __getstate__(self) -> Dict[str, Any]:
        """Do not save the executor and executor function, as it would be cross-referencing and unserializable.
        In other words, a deserialized :class:`BaseExecutableDriver` from file is always unattached. """
        d = super().__getstate__()
        if '_exec' in d:
            del d['_exec']
        if '_exec_fn' in d:
            del d['_exec_fn']
        return d
