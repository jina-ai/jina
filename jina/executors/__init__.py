import os
from types import SimpleNamespace
from typing import Dict, TypeVar, Type, Optional

from .decorators import store_init_kwargs, wrap_func
from .metas import get_default_metas, fill_metas_with_defaults
from .. import __default_endpoint__
from ..helper import typename, random_identity
from ..jaml import JAMLCompatible, JAML, subvar_regex, internal_var_regex

__all__ = ['BaseExecutor', 'AnyExecutor', 'ExecutorType']

AnyExecutor = TypeVar('AnyExecutor', bound='BaseExecutor')


class ExecutorType(type(JAMLCompatible), type):
    """The class of Executor type, which is the metaclass of :class:`BaseExecutor`."""

    def __new__(cls, *args, **kwargs):
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

    .. seealso::
        Methods of the :class:`BaseExecutor` can be decorated via :mod:`jina.executors.decorators`.

    .. seealso::
        Meta fields :mod:`jina.executors.metas.defaults`.

    """

    def __init__(self, metas=None, requests=None, *args, **kwargs):
        super().__init__()
        if metas is None:
            metas = {}
        if requests is not None:
            requests = {}

        self._add_metas(metas)
        self._add_requests(requests)

    def _add_requests(self, _requests: Optional[Dict]):
        if not _requests:
            return

        request_mapping = {}  # type: Dict[str, Callable]
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
        if not _metas:
            return

        unresolved_attr = False
        target = SimpleNamespace()
        # set self values filtered by those non-exist, and non-expandable
        for k, v in _metas.items():
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
            _tmp['metas'] = _metas
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
            _id = random_identity().split('-')[0]
            _name = f'{typename(self)}-{_id}'
            setattr(target, 'name', _name)

        self.metas = target

    def close(self) -> None:
        """
        Release the resources as executor is destroyed, need to be overridden
        """
        pass

    @classmethod
    def _inject_config(
        cls: Type[AnyExecutor],
        raw_config: Dict,
        *args,
        **kwargs,
    ) -> Dict:
        """Inject config into the raw_config before loading into an object.

        :param raw_config: raw config to work on
        :param args: Additional arguments.
        :param kwargs: Additional key word arguments.

        :return: an executor object
        """
        if 'metas' not in raw_config:
            raw_config['metas'] = {}
        tmp = fill_metas_with_defaults(raw_config)
        if kwargs.get('metas'):
            tmp['metas'].update(kwargs['metas'])
            del kwargs['metas']
        tmp.update(kwargs)
        return tmp

    def __call__(self, req_endpoint: str, **kwargs):
        if getattr(self, 'requests', {}):
            if req_endpoint in self.requests:
                return self.requests[req_endpoint](
                    self, **kwargs
                )  # unbound method, self is required
            elif __default_endpoint__ in self.requests:
                return self.requests[__default_endpoint__](
                    self, **kwargs
                )  # unbound method, self is required
            else:
                raise ValueError(
                    f'{req_endpoint} is not bind to any method of {self}. Check for "/".'
                )

    @property
    def workspace(self) -> str:
        """
        Get the path of the current shard.

        :return: returns the workspace of the shard of this Executor.
        """

        pea_id = self.metas.pea_id
        replica_id = self.metas.replica_id
        workspace_folder = self.metas.workspace
        workspace_name = self.metas.name
        if replica_id == -1:
            return os.path.join(workspace_folder, f'{workspace_name}-{pea_id}')
        else:
            return os.path.join(
                workspace_folder, f'{workspace_name}-{replica_id}-{pea_id}'
            )
