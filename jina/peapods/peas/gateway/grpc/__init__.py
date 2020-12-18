import asyncio
import argparse
import os
from multiprocessing.synchronize import Event
from typing import Union, Dict

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

    def __init__(self,
                 args: Union['argparse.Namespace', Dict],
                 ctrl_addr: str,
                 ctrl_with_ipc: bool,
                 **kwargs):
        super().__init__(args, **kwargs)
        self.ctrl_addr = ctrl_addr
        self.ctrl_with_ipc = ctrl_with_ipc

    def run(self, is_ready_event: 'Event'):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        try:
            asyncio.run(self._loop_body(is_ready_event))
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            self._teardown()

    async def _wait_for_shutdown(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
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

    async def serve_forever(self, is_ready_event: 'Event'):
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
        # TODO: proper handling of set_ready
        is_ready_event.set()
        await self.server.wait_for_termination()

    async def _loop_body(self, is_ready_event: 'Event'):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        try:
            await asyncio.gather(self.serve_forever(is_ready_event), self._wait_for_shutdown())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')
        await self.serve_terminate()

    def __enter__(self):
        return self
