import abc
import threading
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING, Dict, Optional, Union

from jina.logging.logger import JinaLogger
from jina.serve.instrumentation import InstrumentationMixin
from jina.serve.runtimes.monitoring import MonitoringMixin

__all__ = ['BaseServer']

if TYPE_CHECKING:
    import multiprocessing

    from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler
    from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler


class BaseServer(MonitoringMixin, InstrumentationMixin):
    """
    BaseServer class that is handled by AsyncNewLoopRuntime. It makes sure that the Request Handler is exposed via a server.
    """

    def __init__(
        self,
        name: Optional[str] = 'gateway',
        runtime_args: Optional[Dict] = None,
        req_handler_cls=None,
        req_handler=None,
        is_cancel=None,
        **kwargs,
    ):
        self.name = name or ''
        self.runtime_args = runtime_args
        self.works_as_load_balancer = False
        self.is_cancel = is_cancel or threading.Event()
        if isinstance(runtime_args, Dict):
            self.works_as_load_balancer = runtime_args.get(
                'gateway_load_balancer', False
            )
        if isinstance(self.runtime_args, dict):
            self.logger = JinaLogger(self.name, **self.runtime_args)
        else:
            self.logger = JinaLogger(self.name, **vars(self.runtime_args))
        self.req_handler_cls = req_handler_cls
        self._request_handler = None
        self.server = None
        self._add_gateway_args()
        self.tracing = self.runtime_args.tracing
        self.tracer_provider = self.runtime_args.tracer_provider
        self._setup_instrumentation(
            name=self.name,
            tracing=self.runtime_args.tracing,
            traces_exporter_host=self.runtime_args.traces_exporter_host,
            traces_exporter_port=self.runtime_args.traces_exporter_port,
            metrics=self.runtime_args.metrics,
            metrics_exporter_host=self.runtime_args.metrics_exporter_host,
            metrics_exporter_port=self.runtime_args.metrics_exporter_port,
        )
        self._request_handler: Union[
            'GatewayRequestHandler', 'WorkerRequestHandler'
        ] = (req_handler or self._get_request_handler())
        if hasattr(self._request_handler, 'streamer'):
            self.streamer = self._request_handler.streamer  # backward compatibility
            self.executor = self._request_handler.executor  # backward compatibility

    def _teardown_instrumentation(self):
        try:
            if self.tracing and self.tracer_provider:
                if hasattr(self.tracer_provider, 'force_flush'):
                    self.tracer_provider.force_flush()
                if hasattr(self.tracer_provider, 'shutdown'):
                    self.tracer_provider.shutdown()
            if self.metrics and self.meter_provider:
                if hasattr(self.meter_provider, 'force_flush'):
                    self.meter_provider.force_flush()
                if hasattr(self.meter_provider, 'shutdown'):
                    self.meter_provider.shutdown()
        except Exception as ex:
            self.logger.warning(f'Exception during instrumentation teardown, {str(ex)}')

    def _get_request_handler(self):
        self._setup_monitoring(
            monitoring=self.runtime_args.monitoring,
            port_monitoring=self.runtime_args.port_monitoring,
        )
        return self.req_handler_cls(
            args=self.runtime_args,
            logger=self.logger,
            metrics_registry=self.metrics_registry,
            meter_provider=self.meter_provider,
            tracer_provider=self.tracer_provider,
            tracer=self.tracer,
            meter=self.meter,
            runtime_name=self.name,
            aio_tracing_client_interceptors=self.aio_tracing_client_interceptors(),
            tracing_client_interceptor=self.tracing_client_interceptor(),
            deployment_name=self.name.split('/')[0],
            works_as_load_balancer=self.works_as_load_balancer,
        )

    def _add_gateway_args(self):
        # TODO: rename and change
        from jina.parsers import set_gateway_runtime_args_parser

        parser = set_gateway_runtime_args_parser()
        default_args = parser.parse_args([])
        default_args_dict = dict(vars(default_args))
        _runtime_args = (
            self.runtime_args
            if isinstance(self.runtime_args, dict)
            else vars(self.runtime_args or {})
        )
        runtime_set_args = {
            'tracer_provider': None,
            'grpc_tracing_server_interceptors': None,
            'runtime_name': _runtime_args.get('name', 'test'),
            'metrics_registry': None,
            'meter': None,
            'aio_tracing_client_interceptors': None,
            'tracing_client_interceptor': None,
        }
        runtime_args_dict = {**runtime_set_args, **default_args_dict, **_runtime_args}
        self.runtime_args = SimpleNamespace(**runtime_args_dict)

    @property
    def port(self):
        """Gets the first port of the port list argument. To be used in the regular case where a Gateway exposes a single port
        :return: The first port to be exposed
        """
        return (
            self.runtime_args.port[0]
            if isinstance(self.runtime_args.port, list)
            else self.runtime_args.port
        )

    @property
    def ports(self):
        """Gets all the list of ports from the runtime_args as a list.
        :return: The lists of ports to be exposed
        """
        return (
            self.runtime_args.port
            if isinstance(self.runtime_args.port, list)
            else [self.runtime_args.port]
        )

    @property
    def protocols(self):
        """Gets all the list of protocols from the runtime_args as a list.
        :return: The lists of protocols to be exposed
        """
        return (
            self.runtime_args.protocol
            if isinstance(self.runtime_args.protocol, list)
            else [self.runtime_args.protocol]
        )

    @property
    def host(self):
        """Gets the host from the runtime_args
        :return: The host where to bind the gateway
        """
        return self.runtime_args.host

    @abc.abstractmethod
    async def setup_server(self):
        """Setup server"""
        ...

    @abc.abstractmethod
    async def run_server(self):
        """Run server forever"""
        ...

    @abc.abstractmethod
    async def shutdown(self):
        """Shutdown the server and free other allocated resources, e.g, streamer object, health check service, ..."""
        self._teardown_instrumentation()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def is_ready(
        ctrl_address: str,
        protocol: Optional[str] = 'grpc',
        timeout: float = 1.0,
        logger=None,
        **kwargs,
    ) -> bool:
        """
        Check if status is ready.
        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param timeout: timeout of grpc call in seconds
        :param logger: JinaLogger to be used
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        from jina.enums import ProtocolType
        from jina.serve.runtimes.servers.grpc import GRPCServer
        from jina.serve.runtimes.servers.http import FastAPIBaseServer

        if protocol is None or protocol == ProtocolType.GRPC or protocol == 'grpc':
            res = GRPCServer.is_ready(ctrl_address)
        else:
            res = FastAPIBaseServer.is_ready(ctrl_address)
        return res

    @staticmethod
    async def async_is_ready(
        ctrl_address: str,
        protocol: Optional[str] = 'grpc',
        timeout: float = 1.0,
        logger=None,
        **kwargs,
    ) -> bool:
        """
        Check if status is ready.
        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param timeout: timeout of grpc call in seconds
        :param logger: JinaLogger to be used
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        from jina.enums import ProtocolType
        from jina.serve.runtimes.servers.grpc import GRPCServer
        from jina.serve.runtimes.servers.http import FastAPIBaseServer

        if protocol is None or protocol == ProtocolType.GRPC or protocol == 'grpc':
            res = await GRPCServer.async_is_ready(ctrl_address, logger=logger)
        else:
            res = await FastAPIBaseServer.async_is_ready(ctrl_address, logger=logger)
        return res

    @classmethod
    def wait_for_ready_or_shutdown(
        cls,
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        ctrl_address: str,
        health_check: bool = False,
        **kwargs,
    ):
        """
        Check if the runtime has successfully started
        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or is ready
        :param health_check: if true, a grpc health check will be used instead of relying on the event
        :param kwargs: extra keyword arguments
        :return: True if is ready or it needs to be shutdown
        """
        timeout_ns = 1000000000 * timeout if timeout else None
        now = time.time_ns()
        if health_check:
            return cls.is_ready(ctrl_address, timeout)
        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            if ready_or_shutdown_event.is_set() or cls.is_ready(ctrl_address, **kwargs):
                return True
            time.sleep(0.1)
        return False
