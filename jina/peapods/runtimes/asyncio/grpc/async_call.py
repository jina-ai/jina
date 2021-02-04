import asyncio

from .....logging import JinaLogger
from .....logging.profile import TimeContext
from .....proto import jina_pb2_grpc
from .....types.message import Message
from .....types.request import Request

__all__ = ['AsyncPrefetchCall']


class AsyncPrefetchCall(jina_pb2_grpc.JinaRPCServicer):

    def __init__(self, args, zmqlet):
        super().__init__()
        self.args = args
        self.zmqlet = zmqlet
        self.name = args.name or self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(args))

    async def Call(self, request_iterator, context):

        def handle(msg: 'Message') -> 'Request':
            msg.add_route(self.name, hex(id(self)))
            return msg.response

        prefetch_task = []

        async def prefetch_req(num_req, fetch_to):
            nf = 0
            async for next_request in request_iterator:
                asyncio.create_task(
                    self.zmqlet.send_message(Message(None, next_request, 'gateway', **vars(self.args))))
                fetch_to.append(asyncio.create_task(self.zmqlet.recv_message(callback=handle)))
                nf += 1
                if nf == num_req:
                    return False  # aiter is not empty yet
            return True  # aiter is empty

        with TimeContext(f'prefetching {self.args.prefetch} requests', self.logger):
            self.logger.warning('if this takes too long, you may want to take smaller "--prefetch" or '
                                'ask client to reduce "--request-size"')
            is_req_empty = await prefetch_req(self.args.prefetch, prefetch_task)
            if is_req_empty and not prefetch_task:
                self.logger.error('receive an empty stream from the client! '
                                  'please check your client\'s input_fn, '
                                  'you can use "Client.check_input(input_fn)"')
                return

        # the total num requests < self.args.prefetch
        if is_req_empty:
            for r in asyncio.as_completed(prefetch_task):
                yield await r
        else:
            # if there are left over (`else` clause above is unnecessary for code but for better readability)
            onrecv_task = []

            # the following code "interleaves" prefetch_task and onrecv_task, when one dries, it switches to the other
            while not is_req_empty:
                self.logger.info(f'send: {self.zmqlet.msg_sent} '
                                 f'recv: {self.zmqlet.msg_recv} '
                                 f'pending: {self.zmqlet.msg_sent - self.zmqlet.msg_recv}')
                onrecv_task.clear()
                for r in asyncio.as_completed(prefetch_task):
                    yield await r
                    if not is_req_empty:
                        is_req_empty = await prefetch_req(self.args.prefetch_on_recv, onrecv_task)

                # this list dries, clear it and feed it with on_recv_task
                prefetch_task.clear()
                prefetch_task = [j for j in onrecv_task]
