import asyncio
import os

import grpc
import zmq.asyncio

from .async_call import AsyncPrefetchCall
from ... import BasePea
from ....zmq import send_message_async, recv_message_async, _init_socket
from .....enums import SocketType
from .....proto import jina_pb2
from .....proto import jina_pb2_grpc

__all__ = ['GatewayPea']


class GatewayPea(BasePea):
    def run(self):
        """Do not overridden this method when inheriting from :class:`GatewayPea`"""
        try:
            asyncio.run(self._loop_body())
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            self._teardown()
            self.unset_ready()
            self.is_shutdown.set()

    async def _wait_for_shutdown(self):
        """Do not overridden this method when inheriting from :class:`GatewayPea`"""
        with zmq.asyncio.Context() as ctx, \
                _init_socket(ctx, self.ctrl_addr, None, SocketType.PAIR_BIND, use_ipc=True)[0] as sock:
            msg = await recv_message_async(sock)
            if msg.request.command == 'TERMINATE':
                msg.envelope.status.code = jina_pb2.StatusProto.SUCCESS
                await self.serve_terminate()
                await send_message_async(sock, msg)

    async def serve_terminate(self):
        """Shutdown the server with async interface

        This method needs to be overridden when inherited from :class:`GatewayPea`
        """
        await self.server.stop(0)

    async def serve_forever(self):
        """Serve an async service forever

        This method needs to be overridden when inherited from :class:`GatewayPea`
        """
        if not self.args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.server = grpc.aio.server(options=[('grpc.max_send_message_length', self.args.max_message_size),
                                               ('grpc.max_receive_message_length', self.args.max_message_size)])
        jina_pb2_grpc.add_JinaRPCServicer_to_server(AsyncPrefetchCall(self.args), self.server)
        bind_addr = f'{self.args.host}:{self.args.port_expose}'
        self.server.add_insecure_port(bind_addr)
        await self.server.start()
        self.logger.success(f'{self.__class__.__name__} is listening at: {bind_addr}')
        self.set_ready()
        await self.server.wait_for_termination()

    async def _loop_body(self):
        """Do not overridden this method when inheriting from :class:`GatewayPea`"""
        try:
            await asyncio.gather(self.serve_forever(), self._wait_for_shutdown())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')
            await self.server.stop(0)
