import asyncio

from .async_stub import AsyncGRPCStub
from jina.peapods.peas import BasePea
from jina.peapods.zmq import CtrlZmqlet, send_message_async, recv_message_async
from jina.helper import configure_event_loop
from jina.proto import jina_pb2


class GatewayPea(BasePea):
    async def _handle_terminate_signal(self):
        with CtrlZmqlet(logger=self.logger, address=self.ctrl_addr) as zmqlet:
            msg = await recv_message_async(sock=zmqlet.sock)
            if msg.request.command == 'TERMINATE':
                msg.envelope.status.code = jina_pb2.StatusProto.SUCCESS
            await send_message_async(sock=zmqlet.sock, msg=msg)
            self._teardown()
            self.is_shutdown.set()

    async def _loop_body(self):
        self.gateway_task = asyncio.create_task(self.gateway.start())
        # we cannot use zmqstreamlet here, as that depends on a custom loop
        self.zmq_task = asyncio.create_task(self._handle_terminate_signal())
        # gateway gets started without awaiting the task, as we don't want to suspend the loop_body here
        # event loop should be suspended depending on zmq ctrl recv, hence awaiting here

        try:
            done_tasks, pending_tasks = await asyncio.wait(
                [self.zmq_task, self.gateway_task], return_when=asyncio.FIRST_COMPLETED)
            if self.gateway_task not in done_tasks:
                await self.gateway.close()
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')
            await self.gateway.close()
            return

    def loop_body(self):
        self.gateway = AsyncGRPCStub(self.args)
        configure_event_loop()
        self.gateway.configure_server(self.args)
        self.set_ready()
        # asyncio.run() or asyncio.run_until_complete() wouldn't work here as we are running a custom loop
        asyncio.get_event_loop().run_until_complete(self._loop_body())

    def _teardown(self):
        if hasattr(self, 'zmq_task'):
            self.zmq_task.cancel()
        if hasattr(self, 'gateway'):
            self.gateway.is_gateway_ready.set()

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            # Every logger created in this process will be identified by the `Pod Id` and use the same name
            self.loop_body()
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            # if an exception occurs this unsets ready and shutting down
            self._teardown()
            self.unset_ready()
            self.is_shutdown.set()
