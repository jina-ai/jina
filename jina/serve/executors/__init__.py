import contextlib
import inspect
import multiprocessing
import os
import threading
import warnings
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from jina import __args_executor_init__, __default_endpoint__
from jina.enums import BetterEnum
from jina.helper import ArgNamespace, T, iscoroutinefunction, typename
from jina.importer import ImportExtensions
from jina.jaml import JAML, JAMLCompatible, env_var_regex, internal_var_regex
from jina.serve.executors.decorators import requests, store_init_kwargs, wrap_func

if TYPE_CHECKING:
    from docarray import DocumentArray
    from prometheus_client import Summary

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
        if cls_id not in reg_cls_set:
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
            def __init__(awesomeness=5):
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
        self._init_monitoring()

    def _add_runtime_args(self, _runtime_args: Optional[Dict]):
        if _runtime_args:
            self.runtime_args = SimpleNamespace(**_runtime_args)
        else:
            self.runtime_args = SimpleNamespace()

    def _init_monitoring(self):
        if (
            hasattr(self.runtime_args, 'metrics_registry')
            and self.runtime_args.metrics_registry
        ):
            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Summary

            self._summary_method = Summary(
                'process_request_seconds',
                'Time spent when calling the executor request method',
                registry=self.runtime_args.metrics_registry,
                namespace='jina',
                labelnames=('executor', 'executor_endpoint', 'runtime_name'),
            )
            self._metrics_buffer = {'process_request_seconds': self._summary_method}

        else:
            self._summary_method = None
            self._metrics_buffer = None

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
        from jina.serve.executors.metas import get_default_metas

        tmp = get_default_metas()

        if _metas:
            tmp.update(_metas)

        unresolved_attr = False
        target = SimpleNamespace()
        # set self values filtered by those non-exist, and non-expandable
        for k, v in tmp.items():
            if k == 'workspace' and not (v is None or v == ''):
                warnings.warn(
                    'Setting `workspace` via `metas.workspace` is deprecated. '
                    'Instead, use `f.add(..., workspace=...)` when defining a a Flow in Python; '
                    'the `workspace` parameter when defining a Flow using YAML; '
                    'or `--workspace` when starting an Executor using the CLI.',
                    category=DeprecationWarning,
                )
            if not hasattr(target, k):
                if isinstance(v, str):
                    if not env_var_regex.findall(v):
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
                            env_var_regex.findall(v) or internal_var_regex.findall(v)
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

    async def __acall__(self, req_endpoint: str, **kwargs):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        if req_endpoint in self.requests:
            return await self.__acall_endpoint__(req_endpoint, **kwargs)
        elif __default_endpoint__ in self.requests:
            return await self.__acall_endpoint__(__default_endpoint__, **kwargs)

    async def __acall_endpoint__(self, req_endpoint, **kwargs):
        func = self.requests[req_endpoint]

        runtime_name = (
            self.runtime_args.name if hasattr(self.runtime_args, 'name') else None
        )

        _summary = (
            self._summary_method.labels(
                self.__class__.__name__, req_endpoint, runtime_name
            ).time()
            if self._summary_method
            else contextlib.nullcontext()
        )

        with _summary:
            if iscoroutinefunction(func):
                return await func(self, **kwargs)
            else:
                return func(self, **kwargs)

    @property
    def workspace(self) -> Optional[str]:
        """
        Get the workspace directory of the Executor.

        :return: returns the workspace of the current shard of this Executor.
        """
        workspace = (
            getattr(self.runtime_args, 'workspace', None)
            or getattr(self.metas, 'workspace')
            or os.environ.get('JINA_DEFAULT_WORKSPACE_BASE')
        )
        if workspace:
            complete_workspace = os.path.join(workspace, self.metas.name)
            shard_id = getattr(
                self.runtime_args,
                'shard_id',
                None,
            )
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

        .. highlight:: python
        .. code-block:: python

            from jina import Executor
            from docarray import Document, DocumentArray

            executor = Executor.from_hub(
                uri='jinahub://CLIPImageEncoder', install_requirements=True
            )

        """
        from jina.hubble.helper import is_valid_huburi

        _source = None
        if is_valid_huburi(uri):
            from jina.hubble.hubio import HubIO
            from jina.parsers.hubble import set_hub_pull_parser

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

    @classmethod
    def serve(
        cls,
        uses_with: Optional[Dict] = None,
        uses_metas: Optional[Dict] = None,
        uses_requests: Optional[Dict] = None,
        stop_event: Optional[Union[threading.Event, multiprocessing.Event]] = None,
        **kwargs,
    ):
        """Serve this Executor in a temporary Flow. Useful in testing an Executor in remote settings.

        :param uses_with: dictionary of parameters to overwrite from the default config's with field
        :param uses_metas: dictionary of parameters to overwrite from the default config's metas field
        :param uses_requests: dictionary of parameters to overwrite from the default config's requests field
        :param stop_event: a threading event or a multiprocessing event that once set will resume the control Flow
            to main thread.
        :param kwargs: other kwargs accepted by the Flow, full list can be found `here <https://docs.jina.ai/api/jina.orchestrate.flow.base/>`

        """
        from jina import Flow

        f = Flow(**kwargs).add(
            uses=cls,
            uses_with=uses_with,
            uses_metas=uses_metas,
            uses_requests=uses_requests,
        )
        with f:
            f.block(stop_event)

    class StandaloneExecutorType(BetterEnum):
        """
        Type of standalone Executors
        """

        EXTERNAL = 0  # served by a gateway
        SHARED = 1  # not served by a gateway, served by head/worker

    @staticmethod
    def to_k8s_yaml(
        uses: str,
        output_base_path: str,
        k8s_namespace: Optional[str] = None,
        executor_type: Optional[
            StandaloneExecutorType
        ] = StandaloneExecutorType.EXTERNAL,
        uses_with: Optional[Dict] = None,
        uses_metas: Optional[Dict] = None,
        uses_requests: Optional[Dict] = None,
        **kwargs,
    ):
        """
        Converts the Executor into a set of yaml deployments to deploy in Kubernetes.

        If you don't want to rebuild image on Jina Hub,
        you can set `JINA_HUB_NO_IMAGE_REBUILD` environment variable.

        :param uses: the Executor to use. Has to be containerized and accessible from K8s
        :param output_base_path: The base path where to dump all the yaml files
        :param k8s_namespace: The name of the k8s namespace to set for the configurations. If None, the name of the Flow will be used.
        :param executor_type: The type of Executor. Can be external or shared. External Executors include the Gateway. Shared Executors don't. Defaults to External
        :param uses_with: dictionary of parameters to overwrite from the default config's with field
        :param uses_metas: dictionary of parameters to overwrite from the default config's metas field
        :param uses_requests: dictionary of parameters to overwrite from the default config's requests field
        :param kwargs: other kwargs accepted by the Flow, full list can be found `here <https://docs.jina.ai/api/jina.orchestrate.flow.base/>`
        """
        from jina import Flow

        f = Flow(**kwargs).add(
            uses=uses,
            uses_with=uses_with,
            uses_metas=uses_metas,
            uses_requests=uses_requests,
        )
        f.to_k8s_yaml(
            output_base_path=output_base_path,
            k8s_namespace=k8s_namespace,
            include_gateway=executor_type
            == BaseExecutor.StandaloneExecutorType.EXTERNAL,
        )

    @staticmethod
    def to_docker_compose_yaml(
        uses: str,
        output_path: Optional[str] = None,
        network_name: Optional[str] = None,
        executor_type: Optional[
            StandaloneExecutorType
        ] = StandaloneExecutorType.EXTERNAL,
        uses_with: Optional[Dict] = None,
        uses_metas: Optional[Dict] = None,
        uses_requests: Optional[Dict] = None,
        **kwargs,
    ):
        """
        Converts the Executor into a yaml file to run with `docker-compose up`
        :param uses: the Executor to use. Has to be containerized
        :param output_path: The output path for the yaml file
        :param network_name: The name of the network that will be used by the deployment name
        :param executor_type: The type of Executor. Can be external or shared. External Executors include the Gateway. Shared Executors don't. Defaults to External
        :param uses_with: dictionary of parameters to overwrite from the default config's with field
        :param uses_metas: dictionary of parameters to overwrite from the default config's metas field
        :param uses_requests: dictionary of parameters to overwrite from the default config's requests field
        :param kwargs: other kwargs accepted by the Flow, full list can be found `here <https://docs.jina.ai/api/jina.orchestrate.flow.base/>`
        """
        from jina import Flow

        f = Flow(**kwargs).add(
            uses=uses,
            uses_with=uses_with,
            uses_metas=uses_metas,
            uses_requests=uses_requests,
        )
        f.to_docker_compose_yaml(
            output_path=output_path,
            network_name=network_name,
            include_gateway=executor_type
            == BaseExecutor.StandaloneExecutorType.EXTERNAL,
        )

    def get_metrics(
        self, name: Optional[str] = None, documentation: Optional[str] = None
    ) -> Optional['Summary']:
        """
        Get a given prometheus metric, if it does not exist yet, it will create it and store it in a buffer.
        :param name: the name of the metrics
        :param documentation:  the description of the metrics

        :return: the given prometheus metrics or None if monitoring is not enable.
        """

        if self._metrics_buffer:
            if name not in self._metrics_buffer:
                from prometheus_client import Summary

                self._metrics_buffer[name] = Summary(
                    name,
                    documentation,
                    registry=self.runtime_args.metrics_registry,
                    namespace='jina',
                    labelnames=('runtime_name',),
                ).labels(self.runtime_args.name)
            return self._metrics_buffer[name]
        else:
            return None


class ReducerExecutor(BaseExecutor):
    """
    ReducerExecutor is an Executor that performs a reduce operation on a matrix of DocumentArrays coming from shards.
    ReducerExecutor relies on DocumentArray.reduce_all to merge all DocumentArray into one DocumentArray which will be
    sent to the next deployment.

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
