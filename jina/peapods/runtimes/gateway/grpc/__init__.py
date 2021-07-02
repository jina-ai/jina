import os

import grpc

from ..prefetch import PrefetchMixin
from ...zmq.asyncio import AsyncNewLoopRuntime
from ....zmq import AsyncZmqlet
from .....logging.logger import JinaLogger
from .....proto import jina_pb2_grpc

__all__ = ['GRPCRuntime']


class GRPCPrefetchCall(PrefetchMixin, jina_pb2_grpc.JinaRPCServicer):
    """JinaRPCServicer """

    def __init__(self, args, zmqlet):
        super().__init__()
        self.args = args
        self.zmqlet = zmqlet
        self.name = args.name or self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(args))


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
        jina_pb2_grpc.add_JinaRPCServicer_to_server(
            GRPCPrefetchCall(self.args, self.zmqlet), self.server
        )
        bind_addr = f'{self.args.host}:{self.args.port_expose}'
        self.server.add_insecure_port(bind_addr)
        await self.server.start()

    async def async_cancel(self):
        """The async method to stop server."""
        await self.server.stop(0)

    async def async_run_forever(self):
        """The async running of server."""
        self.is_ready_event.set()
        await self.server.wait_for_termination()
        self.zmqlet.close()
