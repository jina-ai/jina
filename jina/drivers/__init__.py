import inspect
from functools import wraps
from typing import (
    Any,
    Dict,
    Callable,
    Sequence,
)

from ..executors.decorators import wrap_func
from ..helper import (
    convert_tuple_to_list,
)
from ..jaml import JAMLCompatible
from ..types.sets import DocumentSet

# noinspection PyUnreachableCode
if False:
    # fix type-hint complain for sphinx and flake
    from ..peapods.runtimes.zmq.zed import ZEDRuntime
    from ..logging.logger import JinaLogger
    from ..types.message import Message
    from ..types.request import Request
    from ..types.sets import QueryLangSet


def store_init_kwargs(func: Callable) -> Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML

    :param func: the Callable to wrap
    :return: the wrapped Callable
    """

    @wraps(func)
    def _arg_wrapper(self, *args, **kwargs):
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

    return _arg_wrapper


class DriverType(type(JAMLCompatible), type):
    """A meta class representing a Driver

    When a new Driver is created, it gets registered
    """

    def __new__(cls, *args, **kwargs):
        """Create and register a new class with this meta class.

        :param args: additional positional arguments which are just used for the parent initialization
        :param kwargs: additional key value arguments which are just used for the parent initialization
        :return: the newly registered class
        """
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        """Register a class

        :param cls: the class
        :return: the class, after being registered
        """
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set or getattr(cls, 'force_register', False):
            wrap_func(cls, ['__init__'], store_init_kwargs)
            # wrap_func(cls, ['__call__'], as_reduce_method)

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        return cls


class BaseDriver:

    def attach(self, runtime: 'ZEDRuntime', *args, **kwargs) -> None:
        """Attach this driver to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`

        :param runtime: the pea to be attached
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)
        """
        self.runtime = runtime
        self.attached = True

    @property
    def req(self) -> 'Request':
        """Get the current (typed) request, shortcut to ``self.runtime.request``


        .. # noqa: DAR201
        """
        return self.runtime.request

    @property
    def partial_reqs(self) -> Sequence['Request']:
        """The collected partial requests under the current ``request_id``


        .. # noqa: DAR401


        .. # noqa: DAR201
        """
        if self.expect_parts > 1:
            return self.runtime.partial_requests
        else:
            raise ValueError(
                f'trying to access all partial requests, '
                f'but {self.runtime} has only one message'
            )

    @property
    def expect_parts(self) -> int:
        """The expected number of partial messages


        .. # noqa: DAR201
        """
        return self.runtime.expect_parts

    @property
    def docs(self) -> 'DocumentSet':
        """The DocumentSet after applying the traversal


        .. # noqa: DAR201"""
        from ..types.sets import DocumentSet

        if self.expect_parts > 1:
            return DocumentSet([d for r in reversed(self.partial_reqs) for d in r.docs])
        else:
            return self.req.docs

    @property
    def msg(self) -> 'Message':
        """Get the current request, shortcut to ``self.runtime.message``


        .. # noqa: DAR201
        """
        return self.runtime.message

    @property
    def queryset(self) -> 'QueryLangSet':
        """


        .. # noqa: DAR101


        .. # noqa: DAR102


        .. # noqa: DAR201
        """
        if self.msg:
            return self.msg.request.queryset
        else:
            return []

    @property
    def logger(self) -> 'JinaLogger':
        """Shortcut to ``self.runtime.logger``


        .. # noqa: DAR201
        """
        return self.runtime.logger

    def __call__(self, *args, **kwargs) -> None:
        """


        .. # noqa: DAR102


        .. # noqa: DAR101
        """
        raise NotImplementedError

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __getstate__(self) -> Dict[str, Any]:
        """
        Unlike `Executor`, driver is stateless.

        Therefore, on every save, it creates a new & empty driver object and save it.
        :return: the state in dict form
        """

        d = dict(self.__class__(**self._init_kwargs_dict).__dict__)
        return d
