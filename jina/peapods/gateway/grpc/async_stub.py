import asyncio
import os

import grpc

from .async_servicer import GRPCServicer
from ....logging import JinaLogger
from ....proto import jina_pb2_grpc


class AsyncGRPCStub:
    def __init__(self, args):
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.logger = JinaLogger(context=self.__class__.__name__,
                                 name='gateway',
                                 log_id=args.log_id,
                                 log_config=args.log_config)
        self._p_servicer = GRPCServicer(args)
        self._bind_address = f'{args.host}:{args.port_expose}'

    def configure_server(self, args):
        # event can't be initialized in __init__
        self.is_gateway_ready = asyncio.Event()
        self._server = grpc.aio.server(
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self._p_servicer, self._server)
        self._bind_address = f'{args.host}:{args.port_expose}'
        self._server.add_insecure_port(self._bind_address)

    async def start(self):
        await self._server.start()
        self.logger.success(f'gateway (gRPC) is listening at: {self._bind_address}')
        await self.is_gateway_ready.wait()
        return self

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._server.stop(None)
        self.logger.close()
