import asyncio
import copy
from typing import Any, List, Optional

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
            # ignore metrics_registry since it is not copyable
            runtime_args = self._deepcopy_with_ignore_attrs(
                self.runtime_args, ['metrics_registry']
            )
            runtime_args.port = [port]
            runtime_args.protocol = [protocol]
            gateway_kwargs = {k: v for k, v in kwargs.items() if k != 'runtime_args'}
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

    @property
    def _should_exit(self) -> bool:
        should_exit_values = [
            getattr(gateway.server, 'should_exit', True) for gateway in self.gateways
        ]
        return all(should_exit_values)
