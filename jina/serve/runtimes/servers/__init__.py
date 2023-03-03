import abc
from typing import Dict, Optional

from jina.logging.logger import JinaLogger

__all__ = ['BaseServer']


class BaseServer:

    def __init__(
            self,
            name: Optional[str] = 'gateway',
            runtime_args: Optional[Dict] = None,
            req_handler_cls_name: str = 'GatewayRequestHandler',
            **kwargs,
    ):
        self.name = name
        self.runtime_args = runtime_args
        self.logger = JinaLogger(self.name, **vars(self.runtime_args))
        self._request_handler = None

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
