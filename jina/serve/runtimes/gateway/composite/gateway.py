import asyncio
import copy
from typing import List, Optional

from jina.serve.gateway import BaseGateway


class CompositeGateway(BaseGateway):
    """GRPC Gateway implementation"""

    def __init__(
        self,
        **kwargs,
    ):
        """Initialize the gateway
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)

        from jina.parsers.helper import _get_gateway_class

        self.gateways: List[BaseGateway] = []
        for port, protocol in zip(self.ports, self.protocols):
            gateway_cls = _get_gateway_class(protocol)
            runtime_args = copy.deepcopy(self.runtime_args)
            runtime_args.port = [port]
            runtime_args.protocol = [protocol]
            gateway_kwargs = copy.deepcopy(kwargs)
            gateway_kwargs['runtime_args'] = dict(vars(runtime_args))
            gateway = gateway_cls(**gateway_kwargs)
            self.gateways.append(gateway)

    async def setup_server(self):
        """
        setup GRPC server
        """
        tasks = []
        for gateway in self.gateways:
            tasks.append(asyncio.create_task(gateway.setup_server()))

        await asyncio.gather(*tasks)

    async def shutdown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        shutdown_tasks = []
        for gateway in self.gateways:
            shutdown_tasks.append(asyncio.create_task(gateway.shutdown()))

        await asyncio.gather(*shutdown_tasks)

    async def run_server(self):
        """Run GRPC server forever"""
        run_server_tasks = []
        for gateway in self.gateways:
            run_server_tasks.append(asyncio.create_task(gateway.run_server()))

        await asyncio.gather(*run_server_tasks)

    @property
    def _should_exit(self) -> bool:
        should_exit_values = [
            getattr(gateway.server, 'should_exit', True) for gateway in self.gateways
        ]
        return all(should_exit_values)
