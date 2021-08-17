import argparse
import asyncio
from asyncio import Future
from typing import AsyncGenerator, Dict, Union

from ...grpc import Grpclet
from ....helper import typename, get_or_reuse_loop
from ....logging.logger import JinaLogger
from ....types.message import Message

__all__ = ['PrefetchCaller']

if False:
    from ...zmq import AsyncZmqlet


class PrefetchCaller:
    """An async zmq request sender to be used in the Gateway"""

    def __init__(
        self, args: argparse.Namespace, iolet: Union['AsyncZmqlet', 'Grpclet']
    ):
        """
        :param args: args from CLI
        :param iolet: One of AsyncZmqlet or Grpclet. Used for sending/receiving data to/from the Flow
        """
        self.args = args
        self.name = args.name or self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(args))
        self._message_buffer: Dict[str, Future[Message]] = dict()
        self.iolet = iolet

        if isinstance(iolet, Grpclet):
            self.iolet.callback = self._unwrap_request
            self._receive_task = get_or_reuse_loop().create_task(self.iolet.start())
        else:
            self._receive_task = get_or_reuse_loop().create_task(self._receive())

    async def _unwrap_request(self, msg):
        return self._process_message(msg.request)

    async def _receive(self):
        try:
            while True:
                message = await self.iolet.recv_message(callback=lambda x: x.response)
                # during shutdown the socket will return None
                if message is None:
                    break

                self._process_message(message)
        except asyncio.CancelledError:
            raise
        finally:
            for future in self._message_buffer.values():
                future.cancel(
                    'PrefetchCaller closed, all outstanding requests canceled'
                )
            self._message_buffer.clear()

    def _process_message(self, message):
        if message.request_id in self._message_buffer:
            future = self._message_buffer.pop(message.request_id)
            future.set_result(message)
        else:
            self.logger.warning(
                f'Discarding unexpected message with request id {message.request_id}'
            )

    async def close(self):
        """
        Stop receiving messages
        """
        self._receive_task.cancel()

    async def send(self, request_iterator, *args) -> AsyncGenerator[None, Message]:
        """
        Async call to receive Requests and build them into Messages.

        :param request_iterator: iterator of requests.
        :param args: additional arguments
        :yield: message
        """
        self.args: argparse.Namespace
        self.iolet: Union['AsyncZmqlet', 'Grpclet']
        self.logger: JinaLogger

        if self._receive_task.done():
            raise RuntimeError(
                'PrefetchCaller receive task not running, can not send messages'
            )

        async def prefetch_req(num_req, fetch_to):
            """
            Fetch and send request.

            :param num_req: number of requests
            :param fetch_to: the task list storing requests
            :return: False if append task to :param:`fetch_to` else False
            """
            for _ in range(num_req):
                try:
                    if hasattr(request_iterator, '__anext__'):
                        next_request = await request_iterator.__anext__()
                    elif hasattr(request_iterator, '__next__'):
                        next_request = next(request_iterator)
                    else:
                        raise TypeError(
                            f'{typename(request_iterator)} does not have `__anext__` or `__next__`'
                        )

                    future = get_or_reuse_loop().create_future()
                    self._message_buffer[next_request.request_id] = future
                    asyncio.create_task(
                        self.iolet.send_message(
                            Message(None, next_request, 'gateway', **vars(self.args))
                        )
                    )

                    fetch_to.append(future)
                except (StopIteration, StopAsyncIteration):
                    return True
            return False

        prefetch_task = []
        is_req_empty = await prefetch_req(self.args.prefetch, prefetch_task)
        if is_req_empty and not prefetch_task:
            self.logger.error(
                'receive an empty stream from the client! '
                'please check your client\'s inputs, '
                'you can use "Client.check_input(inputs)"'
            )
            return

        # the total num requests < self.args.prefetch
        if is_req_empty:
            for r in asyncio.as_completed(prefetch_task):
                yield await r
        else:
            # if there are left over (`else` clause above is unnecessary for code but for better readability)
            onrecv_task = []
            # the following code "interleaves" prefetch_task and onrecv_task, when one dries, it switches to the other
            while prefetch_task:
                if self.logger.debug_enabled:
                    self.logger.debug(
                        f'send: {self.iolet.msg_sent} '
                        f'recv: {self.iolet.msg_recv} '
                        f'pending: {self.iolet.msg_sent - self.iolet.msg_recv}'
                    )
                onrecv_task.clear()
                for r in asyncio.as_completed(prefetch_task):
                    yield await r
                    if not is_req_empty:
                        is_req_empty = await prefetch_req(
                            self.args.prefetch_on_recv, onrecv_task
                        )

                # this list dries, clear it and feed it with on_recv_task
                prefetch_task.clear()
                prefetch_task = [j for j in onrecv_task]
