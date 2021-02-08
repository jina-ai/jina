import os

import grpc

from .async_call import AsyncPrefetchCall
from ..base import AsyncNewLoopRuntime
from ....zmq import AsyncZmqlet
from .....proto import jina_pb2_grpc

__all__ = ['GRPCRuntime']


class GRPCRuntime(AsyncNewLoopRuntime):

    async def async_setup(self):
        if not self.args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.server = grpc.aio.server(options=[('grpc.max_send_message_length', self.args.max_message_size),
                                               ('grpc.max_receive_message_length', self.args.max_message_size)])
        self.zmqlet = AsyncZmqlet(self.args, logger=self.logger)
        jina_pb2_grpc.add_JinaRPCServicer_to_server(AsyncPrefetchCall(self.args, self.zmqlet), self.server)
        bind_addr = f'{self.args.host}:{self.args.port_expose}'
        self.server.add_insecure_port(bind_addr)
        await self.server.start()
        self.logger.success(f'{self.__class__.__name__} is listening at: {bind_addr}')

    async def async_cancel(self):
        await self.server.stop(0)

    async def async_run_forever(self):
        await self.server.wait_for_termination()
        self.zmqlet.close()
