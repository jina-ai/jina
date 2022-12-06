import asyncio
import contextlib
import copy
import functools
import inspect
import multiprocessing
import os
import threading
import warnings
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union, overload

from jina import __args_executor_init__, __cache_path__, __default_endpoint__
from jina.enums import BetterEnum
from jina.helper import (
    ArgNamespace,
    T,
    get_or_reuse_loop,
    iscoroutinefunction,
    typename,
)
from jina.importer import ImportExtensions
from jina.jaml import JAML, JAMLCompatible, env_var_regex, internal_var_regex
from jina.logging.logger import JinaLogger
from jina.serve.executors.decorators import (
    _init_requests_by_class,
    avoid_concurrent_lock_cls,
)
from jina.serve.executors.metas import get_executor_taboo
from jina.serve.helper import store_init_kwargs, wrap_func
from jina.serve.instrumentation import MetricsTimer

if TYPE_CHECKING:  # pragma: no cover
    from opentelemetry.context.context import Context

__dry_run_endpoint__ = '_jina_dry_run_'

__all__ = ['BaseExecutor', __dry_run_endpoint__]


class ExecutorType(type(JAMLCompatible), type):
    """The class of Executor type, which is the metaclass of :class:`BaseExecutor`."""

    def __new__(cls, *args, **kwargs):
        """
        # noqa: DAR101
        # noqa: DAR102

        :return: Executor class
        """
        _cls = super().__new__(cls, *args, **kwargs)
        # this needs to be here, in the case where Executors inherited do not define new `requests`
        _init_requests_by_class(_cls)
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
            taboo = get_executor_taboo()

            wrap_func(cls, ['__init__'], store_init_kwargs, taboo=taboo)
            wrap_func(cls, ['__init__'], avoid_concurrent_lock_cls(cls))

            reg_cls_set.add(cls_id)
            setattr(cls, '_registered_class', reg_cls_set)
        return cls


class BaseExecutor(JAMLCompatible, metaclass=ExecutorType):
    """
    The base class of all Executors, can be used to build encoder, indexer, etc.

    :class:`jina.Executor` as an alias for this class.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Executor, requests, Flow


        class MyExecutor(Executor):
            @requests
            def foo(self, docs, **kwargs):
                print(docs)  # process docs here


        f = Flow().add(uses=Executor)  # you can add your Executor to a Flow

    Any executor inherited from :class:`BaseExecutor` always has the **meta** defined in :mod:`jina.executors.metas.defaults`.

    All arguments in the :func:`__init__` can be specified with a ``with`` map in the YAML config. Example:

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeExecutor(Executor):
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
        workspace: Optional[str] = None,
        **kwargs,
    ):
        """`metas` and `requests` are always auto-filled with values from YAML config.

        :param metas: a dict of metas fields
        :param requests: a dict of endpoint-function mapping
        :param runtime_args: a dict of arguments injected from :class:`Runtime` during runtime
        :param kwargs: additional extra keyword arguments to avoid failing when extra params ara passed that are not expected
        :param workspace: the workspace of the executor. Only used if a workspace is not already provided in `metas` or `runtime_args`
        """
        self._add_metas(metas)
        self._add_requests(requests)
        self._add_runtime_args(runtime_args)
        self._init_instrumentation(runtime_args)
        self._init_monitoring()
        self._init_workspace = workspace
        self.logger = JinaLogger(self.__class__.__name__)
        if __dry_run_endpoint__ not in self.requests:
            self.requests[__dry_run_endpoint__] = self._dry_run_func
        else:
            self.logger.warning(
                f' Endpoint {__dry_run_endpoint__} is defined by the Executor. Be aware that this endpoint is usually reserved to enable health checks from the Client through the gateway.'
                f' So it is recommended not to expose this endpoint. '
            )
        if type(self) == BaseExecutor:
            self.requests[__default_endpoint__] = self._dry_run_func

        try:
            self._lock = (
                asyncio.Lock()
            )  # Lock to run in Executor non async methods in a way that does not block the event loop to do health checks without the fear of having race conditions or multithreading issues.
        except RuntimeError:
            self._lock = contextlib.AsyncExitStack()

    def _dry_run_func(self, *args, **kwargs):
        pass

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

        if self.meter:
            self._process_request_histogram = self.meter.create_histogram(
                name='jina_process_request_seconds',
                description='Time spent when calling the executor request method',
            )
            self._histogram_buffer = {
                'jina_process_request_seconds': self._process_request_histogram
            }
        else:
            self._process_request_histogram = None
            self._histogram_buffer = None

    def _init_instrumentation(self, _runtime_args: Optional[Dict] = None):
        if not _runtime_args:
            _runtime_args = {}

        instrumenting_module_name = _runtime_args.get('name', self.__class__.__name__)

        args_tracer_provider = _runtime_args.get('tracer_provider', None)
        if args_tracer_provider:
            self.tracer_provider = args_tracer_provider
            self.tracer = self.tracer_provider.get_tracer(instrumenting_module_name)
        else:
            self.tracer_provider = None
            self.tracer = None

        args_meter_provider = _runtime_args.get('meter_provider', None)
        if args_meter_provider:
            self.meter_provider = args_meter_provider
            self.meter = self.meter_provider.get_meter(instrumenting_module_name)
        else:
            self.meter_provider = None
            self.meter = None

    @property
    def requests(self):
        """
        Get the request dictionary corresponding to this specific class

        :return: Returns the requests corresponding to the specific Executor instance class
        """
        if hasattr(self, '_requests'):
            return self._requests
        else:
            if not hasattr(self, 'requests_by_class'):
                self.requests_by_class = {}
            if self.__class__.__name__ not in self.requests_by_class:
                self.requests_by_class[self.__class__.__name__] = {}
            # we need to copy so that different instances with different (requests) in input do not disturb one another
            self._requests = copy.copy(self.requests_by_class[self.__class__.__name__])
            return self._requests

    def _add_requests(self, _requests: Optional[Dict]):
        if _requests:
            func_names = {f.__name__: e for e, f in self.requests.items()}
            for endpoint, func in _requests.items():
                # the following line must be `getattr(self.__class__, func)` NOT `getattr(self, func)`
                # this to ensure we always have `_func` as unbound method
                if func in func_names:
                    if func_names[func] in self.requests:
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

    async def __acall_endpoint__(
        self, req_endpoint, tracing_context: Optional['Context'], **kwargs
    ):
        func = self.requests[req_endpoint]

        async def exec_func(
            summary, histogram, histogram_metric_labels, tracing_context
        ):
            with MetricsTimer(summary, histogram, histogram_metric_labels):
                if iscoroutinefunction(func):
                    return await func(self, tracing_context=tracing_context, **kwargs)
                else:
                    async with self._lock:
                        return await get_or_reuse_loop().run_in_executor(
                            None,
                            functools.partial(
                                func, self, tracing_context=tracing_context, **kwargs
                            ),
                        )

        runtime_name = (
            self.runtime_args.name if hasattr(self.runtime_args, 'name') else None
        )

        _summary = (
            self._summary_method.labels(
                self.__class__.__name__, req_endpoint, runtime_name
            )
            if self._summary_method
            else None
        )
        _histogram_metric_labels = {
            'executor': self.__class__.__name__,
            'executor_endpoint': req_endpoint,
            'runtime_name': runtime_name,
        }

        if self.tracer:
            with self.tracer.start_as_current_span(
                req_endpoint, context=tracing_context
            ):
                from opentelemetry.propagate import extract
                from opentelemetry.trace.propagation.tracecontext import (
                    TraceContextTextMapPropagator,
                )

                tracing_carrier_context = {}
                TraceContextTextMapPropagator().inject(tracing_carrier_context)
                return await exec_func(
                    _summary,
                    self._process_request_histogram,
                    _histogram_metric_labels,
                    extract(tracing_carrier_context),
                )
        else:
            return await exec_func(
                _summary,
                self._process_request_histogram,
                _histogram_metric_labels,
                None,
            )

    @property
    def workspace(self) -> Optional[str]:
        """
        Get the workspace directory of the Executor.

        :return: returns the workspace of the current shard of this Executor.
        """
        workspace = (
            getattr(self.runtime_args, 'workspace', None)
            or getattr(self.metas, 'workspace')
            or self._init_workspace
            or __cache_path__
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
        from hubble.executor.helper import is_valid_huburi

        _source = None
        if is_valid_huburi(uri):
            from hubble.executor.hubio import HubIO
            from hubble.executor.parsers import set_hub_pull_parser

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

    # overload_inject_start_executor_serve
    @overload
    @classmethod
    def serve(cls, **kwargs):
        """Serve this Executor in a temporary Flow. Useful in testing an Executor in remote settings.

        :param kwargs: other kwargs accepted by the Flow, full list can be found `here <https://docs.jina.ai/api/jina.orchestrate.flow.base/>`
        """

    # overload_inject_end_deployment_serve

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
    def to_kubernetes_yaml(
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

        Flow(**kwargs).add(
            uses=uses,
            uses_with=uses_with,
            uses_metas=uses_metas,
            uses_requests=uses_requests,
        ).to_kubernetes_yaml(
            output_base_path=output_base_path,
            k8s_namespace=k8s_namespace,
            include_gateway=executor_type
            == BaseExecutor.StandaloneExecutorType.EXTERNAL,
        )

    to_k8s_yaml = to_kubernetes_yaml

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

    def monitor(
        self, name: Optional[str] = None, documentation: Optional[str] = None
    ) -> Optional[MetricsTimer]:
        """
        Get a given prometheus metric, if it does not exist yet, it will create it and store it in a buffer.
        :param name: the name of the metrics
        :param documentation:  the description of the metrics

        :return: the given prometheus metrics or None if monitoring is not enable.
        """
        _summary = (
            self._metrics_buffer.get(name, None) if self._metrics_buffer else None
        )
        _histogram = (
            self._histogram_buffer.get(name, None) if self._histogram_buffer else None
        )

        if self._metrics_buffer and not _summary:
            from prometheus_client import Summary

            _summary = Summary(
                name,
                documentation,
                registry=self.runtime_args.metrics_registry,
                namespace='jina',
                labelnames=('runtime_name',),
            ).labels(self.runtime_args.name)
            self._metrics_buffer[name] = _summary

        if self._histogram_buffer and not _histogram:
            _histogram = self.meter.create_histogram(
                name=f'jina_{name}', description=documentation
            )
            self._histogram_buffer[name] = _histogram

        if _summary or _histogram:
            return MetricsTimer(
                _summary,
                _histogram,
                histogram_metric_labels={'runtime_name': self.runtime_args.name},
            )

        return contextlib.nullcontext()
