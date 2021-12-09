from typing import TYPE_CHECKING, Dict, Optional, Type, List, Any
import inspect
import os
from types import SimpleNamespace
from typing import Dict, Optional, Type, List

from .decorators import store_init_kwargs, wrap_func, requests
from .. import __default_endpoint__, __args_executor_init__
from ..helper import typename, ArgNamespace, T
from ..jaml import JAMLCompatible, JAML, subvar_regex, internal_var_regex


if TYPE_CHECKING:
    from jina import DocumentArray


__all__ = ['BaseExecutor', 'ReducerExecutor']


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
        if not hasattr(self, 'requests'):
            self.requests = {}

        if _requests:
            func_names = {f.__name__: e for e, f in self.requests.items()}
            for endpoint, func in _requests.items():
                # the following line must be `getattr(self.__class__, func)` NOT `getattr(self, func)`
                # this to ensure we always have `_func` as unbound method
                if func in func_names:
                    del self.requests[func_names[func]]

                _func = getattr(self.__class__, func)
                if callable(_func):
                    # the target function is not decorated with `@requests` yet
                    self.requests[endpoint] = _func
                elif typename(_func) == 'jina.executors.decorators.FunctionMapper':
                    # the target function is already decorated with `@requests`, need unwrap with `.fn`
                    self.requests[endpoint] = _func.fn
                else:
                    raise TypeError(
                        f'expect {typename(self)}.{func} to be a function, but receiving {typename(_func)}'
                    )

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
    def workspace(self) -> Optional[str]:
        """
        Get the workspace directory of the Executor.

        :return: returns the workspace of the current shard of this Executor.
        """
        workspace = getattr(self.metas, 'workspace') or getattr(
            self.runtime_args, 'workspace', None
        )
        if workspace:
            complete_workspace = os.path.join(workspace, self.metas.name)
            replica_id = getattr(self.runtime_args, 'replica_id', None)
            shard_id = getattr(
                self.runtime_args,
                'shard_id',
                getattr(self.runtime_args, 'pea_id', None),
            )
            if replica_id is not None and replica_id != -1:
                complete_workspace = os.path.join(complete_workspace, str(replica_id))
            if shard_id is not None and shard_id != -1:
                complete_workspace = os.path.join(complete_workspace, str(shard_id))
            if not os.path.exists(complete_workspace):
                os.makedirs(complete_workspace)
            return os.path.abspath(complete_workspace)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def from_hub(
        cls: Type[T],
        uri: str,
        context: Optional[Dict[str, Any]] = None,
        uses_with: Optional[Dict] = None,
        uses_metas: Optional[Dict] = None,
        uses_requests: Optional[Dict] = None,
        **kwargs,
    ) -> T:
        """Construct an Executor from Hub.

        :param uri: a hub Executor scheme starts with `jinahub://`
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :param uses_with: dictionary of parameters to overwrite from the default config's with field
        :param uses_metas: dictionary of parameters to overwrite from the default config's metas field
        :param uses_requests: dictionary of parameters to overwrite from the default config's requests field
        :param kwargs: other kwargs accepted by the CLI ``jina hub pull``
        :return: the Hub Executor object.
        """
        from ..hubble.helper import is_valid_huburi

        _source = None
        if is_valid_huburi(uri):
            from ..hubble.hubio import HubIO
            from ..parsers.hubble import set_hub_pull_parser

            _args = ArgNamespace.kwargs2namespace(
                {'no_usage': True, **kwargs},
                set_hub_pull_parser(),
                positional_args=(uri,),
            )
            _source = HubIO(args=_args).pull()

        if not _source or _source.startswith('docker://'):
            raise ValueError(
                f'Can not construct a native Executor from {uri}. Looks like you want to use it as a '
                f'Docker container, you may want to use it in the Flow via `.add(uses={uri})` instead.'
            )
        return cls.load_config(
            _source,
            context=context,
            uses_with=uses_with,
            uses_metas=uses_metas,
            uses_requests=uses_requests,
        )


class ReducerExecutor(BaseExecutor):
    """
    ReducerExecutor is an Executor that performs a reduce operation on a matrix of DocumentArrays coming from shards.
    ReducerExecutor relies on DocumentArray.reduce_all to merge all DocumentArray into one DocumentArray which will be
    sent to the next pod.

    This Executor only adds a reduce endpoint to the BaseExecutor.
    """

    @requests
    def reduce(self, docs_matrix: List['DocumentArray'] = [], **kwargs):
        """Reduce docs_matrix into one `DocumentArray` using `DocumentArray.reduce_all`
        :param docs_matrix: a List of DocumentArrays to be reduced
        :param kwargs: extra keyword arguments
        :return: the reduced DocumentArray
        """
        if docs_matrix:
            da = docs_matrix[0]
            da.reduce_all(docs_matrix[1:])
            return da
