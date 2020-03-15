import asyncio
import os
import threading

import grpc

from .grpc_asyncio import AsyncioExecutor
from .zmq import AsyncZmqlet, add_envelope
from .. import __stop_msg__
from ..excepts import WaitPendingMessage, EventLoopEnd, NoDriverForRequest, BadRequestType
from ..executors import BaseExecutor
from ..logging.base import get_logger
from ..main.parser import set_pea_parser, set_pod_parser
from ..proto import jina_pb2_grpc, jina_pb2


class FrontendPea:

    def __init__(self, args):
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.logger = get_logger(self.__class__.__name__, **vars(args))
        self.server = grpc.server(
            AsyncioExecutor(),
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])
        if args.allow_spawn:
            self.logger.warning('SECURITY ALERT! this frontend allows SpawnRequest from remote Jina')

        self.p_servicer = self._Pea(args, self.logger)
        jina_pb2_grpc.add_JinaRPCServicer_to_server(self.p_servicer, self.server)
        self.bind_address = '{0}:{1}'.format(args.host, args.port_grpc)
        self.server.add_insecure_port(self.bind_address)
        self._stop_event = threading.Event()
        self.is_ready = threading.Event()

    def __enter__(self):
        self.server.start()
        self.logger.critical('listening at: %s' % self.bind_address)
        self._stop_event.clear()
        self.is_ready.set()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        self.p_servicer.close()
        self.server.stop(None)
        self._stop_event.set()
        self.logger.critical(__stop_msg__)

    def join(self):
        try:
            self._stop_event.wait()
        except KeyboardInterrupt:
            pass

    class _Pea(jina_pb2_grpc.JinaRPCServicer):

        def __init__(self, args, logger):
            super().__init__()
            self.args = args
            self.name = args.name or self.__class__.__name__
            self.logger = logger or get_logger(self.name, **vars(args))
            self.executor = BaseExecutor()
            self.executor.attach(pea=self)
            self.peapods = []

        def recv_callback(self, msg):
            try:
                return self.executor(msg.__class__.__name__)
            except WaitPendingMessage:
                self.logger.error('frontend should not receive partial message, it can not do reduce')
            except EventLoopEnd:
                self.logger.error('event loop end signal should not be raised in the frontend')
            except NoDriverForRequest:
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

        async def Spawn(self, request, context):
            _req = getattr(request, request.WhichOneof('body'))
            if self.args.allow_spawn:
                from ..peapods import Pea, Pod
                _req_type = type(_req)
                if _req_type == jina_pb2.SpawnRequest.PeaSpawnRequest:
                    _args = set_pea_parser().parse_args(_req.args)
                    self.logger.info('starting a BasePea from a remote request')
                    p = Pea(_args)
                elif _req_type == jina_pb2.SpawnRequest.PodSpawnRequest:
                    _args = set_pod_parser().parse_args(_req.args)
                    self.logger.info('starting a BasePod from a remote request')
                    p = Pod(_args)
                elif _req_type == jina_pb2.SpawnRequest.PodDictSpawnRequest:
                    peas_args = {
                        'head': set_pea_parser().parse_args(_req.head.args) if _req.head.args else None,
                        'tail': set_pea_parser().parse_args(_req.tail.args) if _req.tail.args else None,
                        'peas': [set_pea_parser().parse_args(q.args) for q in _req.peas] if _req.peas else []
                    }
                    p = Pod(peas_args)
                else:
                    raise BadRequestType('don\'t know how to handle %r' % _req_type)

                with p:
                    self.peapods.append(p)
                    for l in p.log_iterator:
                        request.log_record = l
                        yield request
                self.peapods.remove(p)
            else:
                warn_msg = f'the frontend at {self.args.host}:{self.args.port_grpc} ' \
                           f'does not support remote spawn, please restart it with --allow_spawn'
                request.log_record = warn_msg
                request.status = jina_pb2.SpawnRequest.ERROR_NOTALLOWED
                self.logger.warning(warn_msg)
                for j in range(1):
                    yield request

        def close(self):
            for p in self.peapods:
                p.close()
