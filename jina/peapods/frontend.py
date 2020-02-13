import asyncio
import os
import threading

import grpc

from .grpc_asyncio import AsyncioExecutor
from .zmq import AsyncZmqlet, add_envelope
from ..drivers import Driver
from ..excepts import WaitPendingMessage, EventLoopEnd, NoRequestHandler
from ..logging.base import get_logger
from ..proto import jina_pb2_grpc


class FrontendPea:

    def __init__(self, args):
        if not args.proxy:
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.logger = get_logger(self.__class__.__name__, **vars(args))
        self.server = grpc.server(
            AsyncioExecutor(),
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])
        jina_pb2_grpc.add_JinaRPCServicer_to_server(self._Pea(args, self.logger), self.server)
        self.bind_address = '{0}:{1}'.format(args.grpc_host, args.grpc_port)
        self.server.add_insecure_port(self.bind_address)
        self._stop_event = threading.Event()

    def __enter__(self):
        self.server.start()
        self.logger.critical('listening at: %s' % self.bind_address)
        self._stop_event.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.stop(None)
        self.stop()

    def stop(self):
        self._stop_event.set()

    def join(self):
        self._stop_event.wait()

    class _Pea(jina_pb2_grpc.JinaRPCServicer):

        def __init__(self, args, logger):
            super().__init__()
            self.args = args
            self.name = args.name or args.driver or self.__class__.__name__
            self.logger = logger or get_logger(self.name, **vars(args))
            self.driver = Driver(self, self.args.driver_yaml_path, self.args.driver)
            self.driver.verify()

        def recv_callback(self, msg):
            try:
                return self.driver.callback(msg)
            except WaitPendingMessage:
                self.logger.error('frontend should not receive partial message, it can not do reduce')
            except EventLoopEnd:
                self.logger.error('event loop end signal should not be raised in the frontend')
            except NoRequestHandler:
                # remove envelope and send back the request
                return msg.request

        async def Call(self, request_iterator, context):
            with AsyncZmqlet(self.args, logger=self.logger) as zmqlet:
                # this restricts the frontend can not be the joiner to wait
                # as every request corresponds to one message, #send_message = #recv_message
                send_tasks, recv_tasks = zip(
                    *[(asyncio.create_task(
                        zmqlet.send_message(
                            add_envelope(request, 'frontend', zmqlet.args.identity),
                            sleep=(self.args.sleep_ms / 1000) * idx, )),
                       zmqlet.recv_message(callback=self.recv_callback))
                        for idx, request in enumerate(request_iterator)])

                for r in asyncio.as_completed(recv_tasks):
                    yield await r


