import asyncio

from ....zmq import AsyncZmqlet
from .....logging import JinaLogger
from .....logging.profile import TimeContext
from .....proto import jina_pb2_grpc
from .....types.message import Message
from .....types.request import Request

__all__ = ['AsyncPrefetchCall']


class AsyncPrefetchCall(jina_pb2_grpc.JinaRPCServicer):

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.name = args.name or self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(args))

    async def Call(self, request_iterator, context):

        def handle(msg: 'Message') -> 'Request':
            msg.add_route(self.name, hex(id(self)))
            return msg.response

        with AsyncZmqlet(self.args, logger=self.logger) as zmqlet:
            # this restricts the gateway can not be the joiner to wait
            # as every request corresponds to one message, #send_message = #recv_message
            prefetch_task = []
            onrecv_task = []

            async def prefetch_req(num_req, fetch_to):
                for _ in range(num_req):
                    try:
                        if hasattr(request_iterator, '__anext__'):
                            # This code block will be executed for gRPC based invocations
                            # An iterator gets converted to a grpc._cython.cygrpc._MessageReceiver object,
                            # which doesn't have a __next__, only an __anext__ method.
                            # If there's any issue with the request_iterator, __anext__() never fails, just hangs.
                            # Adding a default timeout of 2 secs for the anext to avoid hang.
                            # To cancel on large request (will fail/segfault on large request):
                            # await asyncio.wait_for(request_iterator.__anext__(), timeout=2)
                            next_request = await request_iterator.__anext__()
                        elif hasattr(request_iterator, '__next__'):
                            # This code block will be executed for REST based invocations
                            next_request = next(request_iterator)
                        else:
                            break
                        asyncio.create_task(
                            zmqlet.send_message(Message(None, next_request, 'gateway', **vars(self.args))))
                        fetch_to.append(asyncio.create_task(zmqlet.recv_message(callback=handle)))
                    except (StopIteration, StopAsyncIteration):
                        return True
                return False

            with TimeContext(f'prefetching {self.args.prefetch} requests', self.logger):
                self.logger.warning('if this takes too long, you may want to take smaller "--prefetch" or '
                                    'ask client to reduce "--request-size"')
                is_req_empty = await prefetch_req(self.args.prefetch, prefetch_task)
                if is_req_empty and not prefetch_task:
                    self.logger.error('receive an empty stream from the client! '
                                      'please check your client\'s input_fn, '
                                      'you can use "Client.check_input(input_fn)"')
                    return

            while not (zmqlet.msg_sent == zmqlet.msg_recv != 0 and is_req_empty):
                self.logger.info(f'send: {zmqlet.msg_sent} '
                                 f'recv: {zmqlet.msg_recv} '
                                 f'pending: {zmqlet.msg_sent - zmqlet.msg_recv}')
                onrecv_task.clear()
                for r in asyncio.as_completed(prefetch_task):
                    yield await r
                    is_req_empty = await prefetch_req(self.args.prefetch_on_recv, onrecv_task)
                prefetch_task.clear()
                prefetch_task = [j for j in onrecv_task]
