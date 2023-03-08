import abc
from typing import Dict, Optional, Union, TYPE_CHECKING

import time

from jina.logging.logger import JinaLogger
from types import SimpleNamespace

__all__ = ['BaseServer']

if TYPE_CHECKING:
    import multiprocessing
    import threading


class BaseServer:

    def __init__(
            self,
            name: Optional[str] = 'gateway',
            runtime_args: Optional[Dict] = None,
            req_handler_cls=None,
            req_handler=None,
            **kwargs,
    ):
        self.name = name
        self.runtime_args = runtime_args
        self.logger = JinaLogger(self.name, **vars(self.runtime_args))
        self.req_handler_cls = req_handler_cls
        self._request_handler = None
        self.server = None
        self._add_gateway_args()
        self.tracing = self.runtime_args.tracing
        self.tracer_provider = self.runtime_args.tracer_provider
        self.grpc_tracing_server_interceptors = (
            self.runtime_args.grpc_tracing_server_interceptors
        )
        self._request_handler = req_handler or self._get_request_handler()
        if hasattr(self._request_handler, 'streamer'):
            self.streamer = self._request_handler.streamer  # backward compatibility
            self.executor = self._request_handler.executor  # backward compatibility

    def _get_request_handler(self):
        return self.req_handler_cls(
            args=self.runtime_args,
            logger=self.logger,
        )

    def _add_gateway_args(self):
        from jina.parsers import set_gateway_runtime_args_parser
        from jina.parsers import set_pod_parser

        parser = set_gateway_runtime_args_parser()
        default_args = parser.parse_args([])
        default_args_dict = dict(vars(default_args))
        _runtime_args = vars(self.runtime_args or {})
        runtime_set_args = {
            'tracer_provider': None,
            'grpc_tracing_server_interceptors': None,
            'runtime_name': 'test',
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
        return self.runtime_args.port[0]

    @property
    def ports(self):
        """Gets all the list of ports from the runtime_args as a list.
        :return: The lists of ports to be exposed
        """
        return self.runtime_args.port

    @property
    def protocols(self):
        """Gets all the list of protocols from the runtime_args as a list.
        :return: The lists of protocols to be exposed
        """
        return self.runtime_args.protocol

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
        ...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def is_ready(
            ctrl_address: str,
            protocol: Optional[str] = 'grpc',
            timeout: float = 1.0,
            **kwargs,
    ) -> bool:
        """
        Check if status is ready.
        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param timeout: timeout of grpc call in seconds
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        from jina.serve.runtimes.servers.grpc import GRPCServer
        from jina.serve.runtimes.servers.http import FastAPIBaseServer
        from jina.enums import GatewayProtocolType

        if (
                protocol is None
                or protocol == GatewayProtocolType.GRPC
                or protocol == 'grpc'
        ):
            res = GRPCServer.is_ready(ctrl_address)
        else:
            res = FastAPIBaseServer.is_ready(ctrl_address)
        return res

    @staticmethod
    async def async_is_ready(
            ctrl_address: str,
            protocol: Optional[str] = 'grpc',
            timeout: float = 1.0,
            **kwargs,
    ) -> bool:
        """
        Check if status is ready.
        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param timeout: timeout of grpc call in seconds
        :param kwargs: extra keyword arguments
        :return: True if status is ready else False.
        """
        from jina.serve.runtimes.servers.grpc import GRPCServer
        from jina.serve.runtimes.servers.http import FastAPIBaseServer
        from jina.enums import GatewayProtocolType

        if (
                protocol is None
                or protocol == GatewayProtocolType.GRPC
                or protocol == 'grpc'
        ):
            res = await GRPCServer.async_is_ready(ctrl_address)
        else:
            res = await FastAPIBaseServer.async_is_ready(ctrl_address)
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

