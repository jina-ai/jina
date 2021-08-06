import os

import grpc

from jina import __default_host__

from .....proto import jina_pb2_grpc
from ....zmq import AsyncZmqlet
from ...zmq.asyncio import AsyncNewLoopRuntime
from ..prefetch import PrefetchCaller

__all__ = ['GRPCRuntime']


class GRPCPrefetchCall(jina_pb2_grpc.JinaRPCServicer):
    """JinaRPCServicer """

    def __init__(self, args, zmqlet):
        super().__init__()
        self._servicer = PrefetchCaller(args, zmqlet)
        self.Call = self._servicer.send
        self.close = self._servicer.close


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
        self.zmqlet = AsyncZmqlet(self.args, logger=self.logger)
        self._prefetcher = GRPCPrefetchCall(self.args, self.zmqlet)
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
        self.zmqlet.close()
