import inspect
import os
from types import SimpleNamespace
from typing import Dict, TypeVar, Optional, Callable

from .decorators import store_init_kwargs, wrap_func
from .. import __default_endpoint__, __args_executor_init__
from ..helper import typename
from ..jaml import JAMLCompatible, JAML, subvar_regex, internal_var_regex

__all__ = ['BaseExecutor', 'AnyExecutor', 'ExecutorType']

AnyExecutor = TypeVar('AnyExecutor', bound='BaseExecutor')


class ExecutorType(type(JAMLCompatible), type):
    """The class of Executor type, which is the metaclass of :class:`BaseExecutor`."""

    def __new__(cls, *args, **kwargs):
        """
        # noqa: DAR101
        # noqa: DAR102

        :return: Executor class
        """
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        """
        Register a class and wrap update, train, aggregate functions.

        :param cls: The class.
        :return: The class, after being registered.
        """

        reg_cls_set = getattr(cls, '_registered_class', set())

        cls_id = f'{cls.__module__}.{cls.__name__}'
        if cls_id not in reg_cls_set or getattr(cls, 'force_register', False):
            arg_spec = inspect.getfullargspec(cls.__init__)

            if not arg_spec.varkw and not __args_executor_init__.issubset(
                arg_spec.args
            ):
                raise TypeError(
                    f'{cls.__init__} does not follow the full signature of `Executor.__init__`, '
                    f'please add `**kwargs` to your __init__ function'
                )
            wrap_func(cls, ['__init__'], store_init_kwargs)

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

        jtype: MyAwesomeExecutor
        with:
            awesomeness: 5

    """

    def __init__(
        self,
        metas: Optional[Dict] = None,
        requests: Optional[Dict] = None,
        runtime_args: Optional[Dict] = None,
        **kwargs,
    ):
        """`metas` and `requests` are always auto-filled with values from YAML config.

        :param metas: a dict of metas fields
        :param requests: a dict of endpoint-function mapping
        :param runtime_args: a dict of arguments injected from :class:`Runtime` during runtime
        :param kwargs: additional extra keyword arguments to avoid failing when extra params ara passed that are not expected
        """
        self._add_metas(metas)
        self._add_requests(requests)
        self._add_runtime_args(runtime_args)

    def _add_runtime_args(self, _runtime_args: Optional[Dict]):
        if _runtime_args:
            self.runtime_args = SimpleNamespace(**_runtime_args)
        else:
            self.runtime_args = SimpleNamespace()

    def _add_requests(self, _requests: Optional[Dict]):
        request_mapping = {}  # type: Dict[str, Callable]

        if _requests:
            for endpoint, func in _requests.items():
                # the following line must be `getattr(self.__class__, func)` NOT `getattr(self, func)`
                # this to ensure we always have `_func` as unbound method
                _func = getattr(self.__class__, func)
                if callable(_func):
                    # the target function is not decorated with `@requests` yet
                    request_mapping[endpoint] = _func
                elif typename(_func) == 'jina.executors.decorators.FunctionMapper':
                    # the target function is already decorated with `@requests`, need unwrap with `.fn`
                    request_mapping[endpoint] = _func.fn
                else:
                    raise TypeError(
                        f'expect {typename(self)}.{func} to be a function, but receiving {typename(_func)}'
                    )

        if hasattr(self, 'requests'):
            self.requests.update(request_mapping)
        else:
            self.requests = request_mapping

    def _add_metas(self, _metas: Optional[Dict]):
        from .metas import get_default_metas

        tmp = get_default_metas()

        if _metas:
            tmp.update(_metas)

        unresolved_attr = False
        target = SimpleNamespace()
        # set self values filtered by those non-exist, and non-expandable
        for k, v in tmp.items():
            if not hasattr(target, k):
                if isinstance(v, str):
                    if not subvar_regex.findall(v):
                        setattr(target, k, v)
                    else:
                        unresolved_attr = True
                else:
                    setattr(target, k, v)
            elif type(getattr(target, k)) == type(v):
                setattr(target, k, v)

        if unresolved_attr:
            _tmp = vars(self)
            _tmp['metas'] = tmp
            new_metas = JAML.expand_dict(_tmp)['metas']

            for k, v in new_metas.items():
                if not hasattr(target, k):
                    if isinstance(v, str):
                        if not (
                            subvar_regex.findall(v) or internal_var_regex.findall(v)
                        ):
                            setattr(target, k, v)
                        else:
                            raise ValueError(
                                f'{k}={v} is not substitutable or badly referred'
                            )
                    else:
                        setattr(target, k, v)
        # `name` is important as it serves as an identifier of the executor
        # if not given, then set a name by the rule
        if not getattr(target, 'name', None):
            setattr(target, 'name', self.__class__.__name__)

        self.metas = target

    def close(self) -> None:
        """
        Always invoked as executor is destroyed.

        You can write destructor & saving logic here.
        """
        pass

    def __call__(self, req_endpoint: str, **kwargs):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        if req_endpoint in self.requests:
            return self.requests[req_endpoint](
                self, **kwargs
            )  # unbound method, self is required
        elif __default_endpoint__ in self.requests:
            return self.requests[__default_endpoint__](
                self, **kwargs
            )  # unbound method, self is required

    @property
    def workspace(self) -> str:
        """
        Get the path of the current shard.

        :return: returns the workspace of the shard of this Executor.
        """
        workspace = getattr(self.metas, 'workspace') or getattr(
            self.runtime_args, 'workspace', None
        )
        if workspace:
            complete_workspace = os.path.join(workspace, self.metas.name)
            replica_id = getattr(self.runtime_args, 'replica_id', None)
            pea_id = getattr(
                self.runtime_args,
                'pea_id',
                getattr(self.runtime_args, 'shard_id', None),
            )
            if replica_id is not None and replica_id != -1:
                complete_workspace = os.path.join(complete_workspace, str(replica_id))
            if pea_id is not None and pea_id != -1:
                complete_workspace = os.path.join(complete_workspace, str(pea_id))
            if not os.path.exists(complete_workspace):
                os.makedirs(complete_workspace)
            return os.path.abspath(complete_workspace)
        else:
            raise ValueError(
                'Neither `metas.workspace` nor `runtime_args.workspace` is set, '
                'are you using this Executor is a Flow?'
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
