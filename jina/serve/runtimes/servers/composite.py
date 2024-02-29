import asyncio
import copy
from typing import Any, List, TYPE_CHECKING

from jina.serve.runtimes.servers import BaseServer

if TYPE_CHECKING:
    from jina.logging.logger import JinaLogger


class CompositeBaseServer(BaseServer):
    """Composite Base Server implementation from which u can inherit a specific custom composite one"""

    servers: List['BaseServer']
    logger: 'JinaLogger'

    def __init__(
        self,
        **kwargs,
    ):
        """Initialize the gateway
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self._kwargs = kwargs

    @property
    def _server_kwargs(self):
        ret = []
        # ignore monitoring and tracing args since they are not copyable
        ignored_attrs = [
            'metrics_registry',
            'tracer_provider',
            'grpc_tracing_server_interceptors',
            'aio_tracing_client_interceptors',
            'tracing_client_interceptor',
        ]
        for port, protocol in zip(self.ports, self.protocols):
            # ignore monitoring and tracing args since they are not copyable
            runtime_args = self._deepcopy_with_ignore_attrs(
                self.runtime_args, ignored_attrs
            )
            runtime_args.port = port
            runtime_args.protocol = protocol
            server_kwargs = {
                k: v for k, v in self._kwargs.items() if k != 'runtime_args'
            }
            server_kwargs['runtime_args'] = dict(vars(runtime_args))
            server_kwargs['req_handler'] = self._request_handler
            ret.append(server_kwargs)

        return ret

    @staticmethod
    def _deepcopy_with_ignore_attrs(obj: Any, ignore_attrs: List[str]) -> Any:
        """Deep copy an object and ignore some attributes

        :param obj: the object to copy
        :param ignore_attrs: the attributes to ignore
        :return: the copied object
        """

        memo = {}
        for k in ignore_attrs:
            if hasattr(obj, k):
                memo[id(getattr(obj, k))] = None  # getattr(obj, k)

        return copy.deepcopy(obj, memo)

    async def setup_server(self):
        """
        setup servers inside CompositeServer
        """
        self.logger.debug(f'Setting up Composite server')
        tasks = []
        for server in self.servers:
            tasks.append(asyncio.create_task(server.setup_server()))

        await asyncio.gather(*tasks)
        self.logger.debug(f'Composite server setup successful')

    async def shutdown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        self.logger.debug(f'Shutting down server')
        await super().shutdown()
        shutdown_tasks = []
        for server in self.servers:
            shutdown_tasks.append(asyncio.create_task(server.shutdown()))

        await asyncio.gather(*shutdown_tasks)
        self.logger.debug(f'Server shutdown finished')

    async def run_server(self):
        """Run servers inside CompositeServer forever"""
        run_server_tasks = []
        for server in self.servers:
            run_server_tasks.append(asyncio.create_task(server.run_server()))

        await asyncio.gather(*run_server_tasks)

    @property
    def _should_exit(self) -> bool:
        should_exit_values = [
            getattr(server, 'should_exit', True) for server in self.servers
        ]
        return all(should_exit_values)


class CompositeServer(CompositeBaseServer):
    """Composite Server implementation"""

    def __init__(
        self,
        **kwargs,
    ):
        """Initialize the gateway
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        from jina.parsers.helper import _get_gateway_class

        self.servers: List[BaseServer] = []
        for server_kwargs in self._server_kwargs:
            server_cls = _get_gateway_class(
                server_kwargs['runtime_args']['protocol'],
                works_as_load_balancer=self.works_as_load_balancer,
            )
            server = server_cls(**server_kwargs)
            self.servers.append(server)
        self.gateways = self.servers  # for backwards compatibility
