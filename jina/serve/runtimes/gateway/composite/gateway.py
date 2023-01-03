import copy
from typing import List, Optional

from jina.helper import deepcopy_with_ignore_attrs
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
            runtime_args = deepcopy_with_ignore_attrs(self.runtime_args, ['metrics_registry'])
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
        for gateway in self.gateways:
            await gateway.setup_server()

    async def shutdown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        for gateway in self.gateways:
            await gateway.shutdown()

    async def run_server(self):
        """Run GRPC server forever"""
        for gateway in self.gateways:
            await gateway.run_server()

    @property
    def _should_exit(self) -> bool:
        should_exit_values = [
            getattr(gateway.server, 'should_exit', True) for gateway in self.gateways
        ]
        return all(should_exit_values)
