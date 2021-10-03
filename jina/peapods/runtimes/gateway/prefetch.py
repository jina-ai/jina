import argparse
import asyncio
from asyncio import Future
from typing import AsyncGenerator, Dict, List, Union, TYPE_CHECKING

from ...grpc import Grpclet
from ....helper import typename, get_or_reuse_loop
from ....logging.logger import JinaLogger
from ....types.message import Message

__all__ = ['PrefetchCaller']

if TYPE_CHECKING:
    from ...zmq import AsyncZmqlet
    from ....clients.base.http import HTTPClientlet
    from ....types.request import Request, Response


class BasePrefetchCaller:
    """An async zmq request sender to be used in the Gateway"""

    def __init__(
        self,
        args: argparse.Namespace,
        iolet: Union['AsyncZmqlet', 'Grpclet', 'HTTPClientlet'],
    ):
        """
        :param args: args from CLI
        :param iolet: One of AsyncZmqlet or Grpclet. Used for sending/receiving data to/from the Flow
        """
        self.args = args
        self.iolet = iolet
        self.receive_task = self._create_receive_task()
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))

    def _create_receive_task(self) -> asyncio.Task:
        """Start a receive task to be running in the background

        .. # noqa: DAR202
        :return: asyncio Task
        """
        raise NotImplementedError

    async def receive(self):
        """Implement `receive` logic for prefetcher

        .. # noqa: DAR202
        """
        raise NotImplementedError

    def handle_request(self, request: 'Request', fetch_to: List):
        """Handle each request in the iterator

        :param request: current request in the iterator
        :param fetch_to: list to add the task to
        """
        raise NotImplementedError

    async def close(self):
        """
        Stop receiving messages
        """
        self.receive_task.cancel()

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

        if self.receive_task.done():
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
                        request = await request_iterator.__anext__()
                    elif hasattr(request_iterator, '__next__'):
                        request = next(request_iterator)
                    else:
                        raise TypeError(
                            f'{typename(request_iterator)} does not have `__anext__` or `__next__`'
                        )

                    self.handle_request(request=request, fetch_to=fetch_to)
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


class ZmqPrefetchCaller(BasePrefetchCaller):
    def __init__(
        self,
        args: argparse.Namespace,
        iolet: Union['AsyncZmqlet', 'Grpclet', 'HTTPClientlet'],
    ):
        super().__init__(args, iolet)
        self.request_buffer: Dict[str, Future[Message]] = dict()
        self.Call = self.send  # Used in

    def _create_receive_task(self):
        """Start a receive task that starts the GRPC server & awaits termination.

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(self.receive())

    def convert_to_message(self, request: 'Request'):
        """Convert a `Request` to a `Message` to be sent from gateway

        :param request: request from iterator
        :return: Message from request
        """
        return Message(None, request, 'gateway', **vars(self.args))

    def handle_request(self, request: 'Request', fetch_to: List):
        """
        For ZMQ & GRPC data requests, for each request in the iterator, we send the `Message` using
        `iolet.send_message()` and add {<request-id>: <an-empty-future>} to the message buffer.
        This empty future is used to track the `result` of this request during `receive`

        :param request: current request in the iterator
        :param fetch_to: list to add the task to
        """
        future = get_or_reuse_loop().create_future()
        self.request_buffer[request.request_id] = future
        asyncio.create_task(
            self.iolet.send_message(self.convert_to_message(request=request))
        )
        fetch_to.append(future)

    async def receive(self):
        """Await messages back from Executors and process them in the message buffer"""
        try:
            while True:
                response = await self.iolet.recv_message(callback=lambda x: x.response)
                # during shutdown the socket will return None
                if response is None:
                    break

                self.handle_response(response)
        except asyncio.CancelledError:
            raise
        finally:
            for future in self.request_buffer.values():
                future.cancel(
                    f'{self.__class__.__name__} closed, all outstanding requests canceled'
                )
            self.request_buffer.clear()

    def handle_response(self, response: 'Response'):
        """
        Set result of each response received from Executors in the request buffer

        :param response: message received during `iolet.recv_message`
        """
        if response.request_id in self.request_buffer:
            future = self.request_buffer.pop(response.request_id)
            future.set_result(response)
        else:
            self.logger.warning(
                f'Discarding unexpected response with request id {response.request_id}'
            )


class GrpcPrefetchCaller(ZmqPrefetchCaller):
    def __init__(self, args: argparse.Namespace, iolet: 'Grpclet'):
        super().__init__(args, iolet)
        self.iolet.callback = lambda response: self.handle_response(response.request)

    def _create_receive_task(self) -> 'asyncio.Task':
        """Start a receive task that starts the GRPC server & awaits termination.

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(self.iolet.start())


class HTTPClientPrefetchCaller(BasePrefetchCaller):
    def convert_to_message(self, request: 'Request', **kwargs):
        """Convert request to dict for POST request

        :param request: request from client
        :param kwargs: keyword args
        :return: request as dict
        """
        req_dict = request.dict()
        req_dict['exec_endpoint'] = req_dict['header']['exec_endpoint']
        req_dict['data'] = req_dict['data'].get('docs', None)
        return req_dict

    def handle_request(self, request: 'Request', fetch_to: List):
        """
        For HTTP Client, for each request in the iterator, we send the message (http POST request)
        and add it to the list of tasks which is awaited.

        :param request: current request in the iterator
        :param fetch_to: list to add the task to
        """
        fetch_to.append(
            asyncio.create_task(
                self.iolet.send_message(self.convert_to_message(request=request))
            )
        )

    def _create_receive_task(self) -> 'asyncio.Task':
        """For HTTP Client, there's no task needed for receiving. Sleep like there's no tomorrow!

        :return: asyncio Task
        """
        return get_or_reuse_loop().create_task(asyncio.sleep(1e9))
