import abc
from typing import Dict, Optional

from jina.logging.logger import JinaLogger
from types import SimpleNamespace

__all__ = ['BaseServer']


class BaseServer:

    def __init__(
            self,
            name: Optional[str] = 'gateway',
            runtime_args: Optional[Dict] = None,
            req_handler_cls=None,
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
        self._request_handler = self._get_request_handler()
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
