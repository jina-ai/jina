import asyncio
import os

import grpc

from .servicer import GRPCServicer
from ..pea import BasePea
from ..zmq import AsyncCtrlZmqlet, send_message_async, recv_message_async
from ...helper import use_uvloop
from ...logging import JinaLogger
from ...proto import jina_pb2_grpc, jina_pb2


class GatewayPea(BasePea):
    async def handle_terminate_signal(self):
        with AsyncCtrlZmqlet(args=self.args, logger=self.logger, ctrl_addr=self.ctrl_addr) as zmqlet:
            msg = await recv_message_async(sock=zmqlet.ctrl_sock)
            if msg.request.command == 'TERMINATE':
                msg.envelope.status.code = jina_pb2.StatusProto.SUCCESS
            await send_message_async(sock=zmqlet.ctrl_sock, msg=msg)
            self.loop_teardown()
            self.is_shutdown.set()

    async def _loop_body(self):
        asyncio.get_event_loop().create_task(self.gateway.start()) \
            if asyncio.iscoroutinefunction(self.gateway.start) \
            else self.gateway.start()

        # we cannot use zmqstreamlet here, as that depends on a custom loop
        self.zmq_task = asyncio.get_running_loop().create_task(self.handle_terminate_signal())
        # gateway gets started without awaiting the task, as we don't want to suspend the loop_body here
        # event loop should be suspended depending on zmq ctrl recv, hence awaiting here
        try:
            await self.zmq_task
        except asyncio.CancelledError:
            self.logger.debug('received terminate ctrl message from main process')

    def loop_body(self):
        self.gateway = AsyncGateway(self.args)
        self.set_ready()
        # asyncio.run() or asyncio.run_until_complete() wouldn't work here as we are running a custom loop
        asyncio.get_event_loop().run_until_complete(self._loop_body())

    async def _loop_teardown(self):
        asyncio.get_event_loop().create_task(self.gateway.close()) \
            if asyncio.iscoroutinefunction(self.gateway.close) \
            else self.gateway.close()

    def loop_teardown(self):
        self.zmq_task.cancel()
        if hasattr(self, 'gateway'):
            self.gateway.is_gateway_ready.set()
            # asyncio.get_event_loop().run_until_complete(self._loop_teardown())


class AsyncGateway:
    def __init__(self, args):
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.logger = JinaLogger(context=self.__class__.__name__,
                                 name='gateway',
                                 log_id=args.log_id,
                                 log_config=args.log_config)
        self._p_servicer = GRPCServicer(args)
        self.configure_event_loop()
        self.is_gateway_ready = asyncio.Event()
        self.init_server(args)

    @staticmethod
    def configure_event_loop():
        use_uvloop()
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())

    def init_server(self, args):
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
