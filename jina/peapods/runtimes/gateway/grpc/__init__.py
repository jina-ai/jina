import os

import grpc

from jina import __default_host__
from ....grpc import Grpclet

from .....proto import jina_pb2_grpc
from ....zmq import AsyncZmqlet
from ...zmq.asyncio import AsyncNewLoopRuntime
from ...prefetch.gateway import GrpcGatewayPrefetcher, ZmqGatewayPrefetcher

__all__ = ['GRPCRuntime']


class GRPCRuntime(AsyncNewLoopRuntime):
    """Runtime for gRPC."""

    async def async_setup(self):
        """
        The async method to setup.

        Create the gRPC server and expose the port for communication.
        """
        if not self.args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        if self.args.grpc_data_requests:
            self._grpclet = Grpclet(
                args=self.args,
                message_callback=None,
                logger=self.logger,
            )
            self._prefetcher = GrpcGatewayPrefetcher(self.args, iolet=self._grpclet)
        else:
            self.zmqlet = AsyncZmqlet(self.args, logger=self.logger)
            self._prefetcher = ZmqGatewayPrefetcher(self.args, iolet=self.zmqlet)

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self._prefetcher, self.server)
        bind_addr = f'{__default_host__}:{self.args.port_expose}'
        self.server.add_insecure_port(bind_addr)
        await self.server.start()

    async def async_cancel(self):
        """The async method to stop server."""
        await self.server.stop(0)
        await self._prefetcher.close()

    async def async_run_forever(self):
        """The async running of server."""
        await self.server.wait_for_termination()
        if self.args.grpc_data_requests:
            await self._grpclet.close()
        else:
            self.zmqlet.close()
