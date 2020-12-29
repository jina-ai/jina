import asyncio
from abc import ABC

import zmq.asyncio

from ..zmq.base import ZMQRuntime
from ...zmq import _init_socket, recv_message_async, send_message_async
from ....enums import SocketType
from ....proto import jina_pb2


class AsyncZMQRuntime(ZMQRuntime):

    def run_forever(self):
        asyncio.run(self._loop_body())

    async def async_cancel(self):
        raise NotImplementedError

    async def async_run_forever(self):
        raise NotImplementedError

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        with zmq.asyncio.Context() as ctx, \
                _init_socket(ctx, self.ctrl_addr, None, SocketType.PAIR_BIND, use_ipc=True)[0] as sock:
            msg = await recv_message_async(sock)
            if msg.request.command == 'TERMINATE':
                msg.envelope.status.code = jina_pb2.StatusProto.SUCCESS
                await self.async_cancel()
                await send_message_async(sock, msg)

    async def _loop_body(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        try:
            await asyncio.gather(self.async_run_forever(), self._wait_for_cancel())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')
        await self.async_cancel()


class AsyncNewLoopRuntime(AsyncZMQRuntime, ABC):

    def run_forever(self):
        self._loop.run_until_complete(self._loop_body())

    def setup(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.async_setup())

    def teardown(self):
        self._loop.stop()
        self._loop.close()

    async def async_setup(self):
        pass
