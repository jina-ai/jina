__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from functools import wraps
from typing import (
    Any,
    Dict,
    Callable,
    Tuple,
    Optional,
    Sequence,
)

from google.protobuf.struct_pb2 import Struct

from ..enums import OnErrorStrategy
from ..executors import BaseExecutor
from ..executors.compound import CompoundExecutor
from ..executors.decorators import wrap_func
from ..helper import convert_tuple_to_list
from ..jaml import JAMLCompatible

if False:
    # fix type-hint complain for sphinx and flake
    from ..peapods.runtimes.zmq.zed import ZEDRuntime
    from ..executors import AnyExecutor
    from ..logging.logger import JinaLogger
    from ..types.message import Message
    from ..types.document import Document
    from ..types.request import Request
    from ..types.sets import QueryLangSet, DocumentSet


def store_init_kwargs(func: Callable) -> Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError(
                'this decorator should only be used on __init__ method of a driver'
            )
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
            if args:
                tmp['args'] = args
            if kwargs:
                tmp['kwargs'] = {k: v for k, v in kwargs.items() if k not in taboo}

        if hasattr(self, '_init_kwargs_dict'):
            self._init_kwargs_dict.update(tmp)
        else:
            self._init_kwargs_dict = tmp
        convert_tuple_to_list(self._init_kwargs_dict)
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper


class QuerySetReader:
    """:class:`QuerySetReader` allows a driver to read arguments from the protobuf message. This allows a
    driver to override its behavior based on the message it receives. Extremely useful in production, for example,
    get ``top_k`` results, doing pagination, filtering.

    To register the field you want to read from the message, simply register them in :meth:`__init__`.
    For example, ``__init__(self, arg1, arg2, **kwargs)`` will allow the driver to read field ``arg1`` and ``arg2`` from
    the message. When they are not found in the message, the value ``_arg1`` and ``_arg2`` will be used. Note the underscore
    prefix.

    .. note::
        - To set default value of ``arg1``, use ``self._arg1 =``, note the underscore in the front.
        - To access ``arg1``, simply use ``self.arg1``. It automatically switch between default ``_arg1`` and ``arg1`` from the request.

    For successful value reading, the following condition must be met:

        - the ``name`` in the proto must match with the current class name
        - the ``disabled`` field in the proto should not be ``False``
        - the ``priority`` in the proto should be strictly greater than the driver's priority (by default is 0)
        - the field name must exist in proto's ``parameters``

    .. warning::
        For the sake of cooperative multiple inheritance, do NOT implement :meth:`__init__` for this class

    """

    def _get_parameter(self, key: str, default: Any):
        if getattr(self, 'queryset', None):
            for q in self.queryset:
                if (
                    not q.disabled
                    and self.__class__.__name__ == q.name
                    and q.priority > self._priority
                    and key in q.parameters
                ):
                    ret = q.parameters[key]
                    return dict(ret) if isinstance(ret, Struct) else ret
        return getattr(self, f'_{key}', default)

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if name == '_init_kwargs_dict':
            # raise attribute error to avoid recursive call
            raise AttributeError
        if name in self._init_kwargs_dict:
            return self._get_parameter(name, default=self._init_kwargs_dict[name])
        raise AttributeError


class DriverType(type(JAMLCompatible), type):
    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set or getattr(cls, 'force_register', False):
            wrap_func(cls, ['__init__'], store_init_kwargs)
            # wrap_func(cls, ['__call__'], as_reduce_method)

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        return cls


class BaseDriver(JAMLCompatible, metaclass=DriverType):
    """A :class:`BaseDriver` is a logic unit above the :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.
    It reads the protobuf message, extracts/modifies the required information and then return
    the message back to :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.

    A :class:`BaseDriver` needs to be :attr:`attached` to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` before
    using. This is done by :func:`attach`. Note that a deserialized :class:`BaseDriver` from file is always unattached.

    """

    store_args_kwargs = False  #: set this to ``True`` to save ``args`` (in a list) and ``kwargs`` (in a map) in YAML config

    def __init__(self, priority: int = 0, *args, **kwargs):
        """

        :param priority: the priority of its default arg values (hardcoded in Python). If the
             received ``QueryLang`` has a higher priority, it will override the hardcoded value
        """
        self.attached = False  # : represent if this driver is attached to a
        # :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` (& :class:`jina.executors.BaseExecutor`)
        self.runtime = None  # type: Optional['ZEDRuntime']
        self._priority = priority

    def attach(self, runtime: 'ZEDRuntime', *args, **kwargs) -> None:
        """Attach this driver to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`

        :param runtime: the pea to be attached.
        """
        self.runtime = runtime
        self.attached = True

    @property
    def req(self) -> 'Request':
        """Get the current (typed) request, shortcut to ``self.runtime.request``"""
        return self.runtime.request

    @property
    def partial_reqs(self) -> Sequence['Request']:
        """The collected partial requests under the current ``request_id`` """
        if self.expect_parts > 1:
            return self.runtime.partial_requests
        else:
            raise ValueError(
                f'trying to access all partial requests, '
                f'but {self.runtime} has only one message'
            )

    @property
    def expect_parts(self) -> int:
        """The expected number of partial messages """
        return self.runtime.expect_parts

    @property
    def msg(self) -> 'Message':
        """Get the current request, shortcut to ``self.runtime.message``"""
        return self.runtime.message

    @property
    def queryset(self) -> 'QueryLangSet':
        if self.msg:
            return self.msg.request.queryset
        else:
            return []

    @property
    def docs(self):
        if self.expect_parts > 1:
            return (d for r in reversed(self.partial_reqs) for d in r.docs)
        else:
            return self.req.docs

    @property
    def logger(self) -> 'JinaLogger':
        """Shortcut to ``self.runtime.logger``"""
        return self.runtime.logger

    def __call__(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @staticmethod
    def _dump_instance_to_yaml(data) -> Dict[str, Dict]:
        # note: we only save non-default property for the sake of clarity
        a = {k: v for k, v in data._init_kwargs_dict.items()}
        r = {}
        if a:
            r['with'] = a
        return r

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __getstate__(self) -> Dict[str, Any]:
        """
        Unlike `Executor`, driver is stateless.

        Therefore, on every save, it creates a new & empty driver object and save it.
        """

        d = dict(self.__class__(**self._init_kwargs_dict).__dict__)
        return d


class BaseRecursiveDriver(BaseDriver):
    def __init__(self, traversal_paths: Tuple[str] = ('c', 'r'), *args, **kwargs):
        """
        :param traversal_paths: The describes the leaves of the document tree on which _apply_all are called
        """
        super().__init__(*args, **kwargs)
        self._traversal_paths = [path.lower() for path in traversal_paths]

    def _apply_root(
        self,
        docs: 'DocumentSet',
        field: str,
        *args,
        **kwargs,
    ) -> None:
        return self._apply_all(docs, None, field, *args, **kwargs)

    # TODO(Han): probably want to publicize this, as it is not obvious for driver
    #  developer which one should be inherited
    def _apply_all(
        self,
        docs: 'DocumentSet',
        context_doc: 'Document',
        field: str,
        *args,
        **kwargs,
    ) -> None:
        """Apply function works on a list of docs, modify the docs in-place

        :param docs: a list of :class:`jina.Document` objects to work on; they could come from ``matches``/``chunks``.
        :param context_doc: the owner of ``docs``
        :param field: where ``docs`` comes from, either ``matches`` or ``chunks``
        """

    def __call__(self, *args, **kwargs):
        self._traverse_apply(self.docs, *args, **kwargs)

    def _traverse_apply(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        for path in self._traversal_paths:
            if path[0] == 'r':
                self._apply_root(docs, 'docs', *args, **kwargs)
            for doc in docs:
                self._traverse_rec(
                    [doc],
                    None,
                    None,
                    path,
                    *args,
                    **kwargs,
                )

    def _traverse_rec(self, docs, parent_doc, parent_edge_type, path, *args, **kwargs):
        if path:
            next_edge = path[0]
            for doc in docs:
                if next_edge == 'm':
                    self._traverse_rec(
                        doc.matches, doc, 'matches', path[1:], *args, **kwargs
                    )
                if next_edge == 'c':
                    self._traverse_rec(
                        doc.chunks, doc, 'chunks', path[1:], *args, **kwargs
                    )
        else:
            self._apply_all(docs, parent_doc, parent_edge_type, *args, **kwargs)


class BaseExecutableDriver(BaseRecursiveDriver):
    """A :class:`BaseExecutableDriver` is an intermediate logic unit between the :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` and :class:`jina.executors.BaseExecutor`
    It reads the protobuf message, extracts/modifies the required information and then sends to the :class:`jina.executors.BaseExecutor`,
    finally it returns the message back to :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.

    A :class:`BaseExecutableDriver` needs to be :attr:`attached` to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` and :class:`jina.executors.BaseExecutor` before using.
    This is done by :func:`attach`. Note that a deserialized :class:`BaseDriver` from file is always unattached.
    """

    def __init__(self, executor: str = None, method: str = None, *args, **kwargs):
        """Initialize a :class:`BaseExecutableDriver`

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
        if (
            not self.msg.is_error
            or self.runtime.args.on_error_strategy < OnErrorStrategy.SKIP_EXECUTOR
        ):
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
                    if any(
                        t.__name__ == self._executor_name for t in type.mro(c.__class__)
                    ):
                        self._exec = c
                        break
            if self._exec is None:
                self.logger.critical(
                    f'fail to attach the driver to {executor}, '
                    f'no executor is named or typed as {self._executor_name}'
                )
        else:
            self._exec = executor

        if self._method_name:
            if self._method_name not in BaseExecutor.exec_methods:
                self.logger.warning(
                    f'Using method {self._method_name} as driver execution function which is not registered'
                    f'as a potential `exec_method` of an Executor. It won\'t work if used inside a CompoundExecutor'
                )

            self._exec_fn = getattr(self.exec, self._method_name)

    def __getstate__(self) -> Dict[str, Any]:
        """Do not save the executor and executor function, as it would be cross-referencing and unserializable.
        In other words, a deserialized :class:`BaseExecutableDriver` from file is always unattached."""
        d = super().__getstate__()
        if '_exec' in d:
            del d['_exec']
        if '_exec_fn' in d:
            del d['_exec_fn']
        return d
