__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
import os
import threading

import grpc

from jina.logging.profile import TimeContext
from .grpc_asyncio import AsyncioExecutor
from .zmq import AsyncZmqlet, add_envelope
from .. import __stop_msg__
from ..excepts import NoExplicitMessage, RequestLoopEnd, NoDriverForRequest, BadRequestType
from ..executors import BaseExecutor
from ..logging.base import get_logger
from ..main.parser import set_pea_parser, set_pod_parser
from ..proto import jina_pb2_grpc, jina_pb2


class GatewayPea:
    """A :class:`BasePea`-like class for holding Gateway.

    It has similar :meth:`start` and context interface as :class:`BasePea`,
    but it is not built on thread or process. It works directly in the main thread main process.

    This is because (1) asyncio does not
    work properly on multi-thread (2) spawn another process in a daemon process
    is not allowed.
    """

    def __init__(self, args):
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.logger = get_logger(self.__class__.__name__, **vars(args))
        if args.allow_spawn:
            self.logger.critical('SECURITY ALERT! this gateway allows SpawnRequest from remote Jina')
        self._server = grpc.server(
            AsyncioExecutor(),
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])

        self._p_servicer = self._Pea(args)
        jina_pb2_grpc.add_JinaRPCServicer_to_server(self._p_servicer, self._server)
        self._bind_address = '{0}:{1}'.format(args.host, args.port_grpc)
        self._server.add_insecure_port(self._bind_address)
        self._stop_event = threading.Event()
        self.is_ready = threading.Event()

    def __enter__(self):
        return self.start()

    def start(self):
        self._server.start()
        self.logger.success('gateway is listening at: %s' % self._bind_address)
        self._stop_event.clear()
        self.is_ready.set()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._p_servicer.close()
        self._server.stop(None)
        self._stop_event.set()
        self.logger.success(__stop_msg__)

    def join(self):
        try:
            self._stop_event.wait()
        except KeyboardInterrupt:
            pass

    class _Pea(jina_pb2_grpc.JinaRPCServicer):

        def __init__(self, args):
            super().__init__()
            self.args = args
            self.name = args.name or self.__class__.__name__
            self.logger = get_logger(self.name, **vars(args))
            self.executor = BaseExecutor()
            self.executor.attach(pea=self)
            self.peapods = []

        def recv_callback(self, msg):
            try:
                return self.executor(msg.__class__.__name__)
            except NoExplicitMessage:
                self.logger.error('gateway should not receive partial message, it can not do reduce')
            except RequestLoopEnd:
                self.logger.error('event loop end signal should not be raised in the gateway')
            except NoDriverForRequest:
                # remove envelope and send back the request
                return msg.request

        async def CallUnary(self, request, context):
            with AsyncZmqlet(self.args, logger=self.logger) as zmqlet:
                await zmqlet.send_message(add_envelope(request, 'gateway', zmqlet.args.identity))
                return await zmqlet.recv_message(callback=self.recv_callback)

        async def Call(self, request_iterator, context):
            with AsyncZmqlet(self.args, logger=self.logger) as zmqlet:
                # this restricts the gateway can not be the joiner to wait
                # as every request corresponds to one message, #send_message = #recv_message
                prefetch_task = []
                onrecv_task = []

                def prefetch_req(num_req, fetch_to):
                    for _ in range(num_req):
                        try:
                            asyncio.create_task(
                                zmqlet.send_message(
                                    add_envelope(next(request_iterator), 'gateway', zmqlet.args.identity)))
                            fetch_to.append(asyncio.create_task(zmqlet.recv_message(callback=self.recv_callback)))
                        except StopIteration:
                            return True
                    return False

                with TimeContext(f'prefetching {self.args.prefetch} requests', self.logger):
                    self.logger.warning('if this takes too long, you may want to take smaller "--prefetch" or '
                                        'ask client to reduce "--batch-size"')
                    is_req_empty = prefetch_req(self.args.prefetch, prefetch_task)

                while not (zmqlet.msg_sent == zmqlet.msg_recv != 0 and is_req_empty):
                    self.logger.info(f'send: {zmqlet.msg_sent} '
                                     f'recv: {zmqlet.msg_recv} '
                                     f'pending: {zmqlet.msg_sent - zmqlet.msg_recv}')
                    onrecv_task.clear()
                    for r in asyncio.as_completed(prefetch_task):
                        yield await r
                        is_req_empty = prefetch_req(self.args.prefetch_on_recv, onrecv_task)
                    prefetch_task.clear()
                    prefetch_task = [j for j in onrecv_task]

        async def Spawn(self, request, context):
            _req = getattr(request, request.WhichOneof('body'))
            if self.args.allow_spawn:
                from . import Pea, Pod
                _req_type = type(_req)
                if _req_type == jina_pb2.SpawnRequest.PeaSpawnRequest:
                    _args = set_pea_parser().parse_known_args(_req.args)[0]
                    self.logger.info('starting a BasePea from a remote request')
                    # we do not allow remote spawn request to spawn a "remote-remote" pea/pod
                    p = Pea(_args, allow_remote=False)
                elif _req_type == jina_pb2.SpawnRequest.PodSpawnRequest:
                    _args = set_pod_parser().parse_known_args(_req.args)[0]
                    self.logger.info('starting a BasePod from a remote request')
                    # need to return the new port and host ip number back
                    # we do not allow remote spawn request to spawn a "remote-remote" pea/pod
                    p = Pod(_args, allow_remote=False)
                    from .remote import peas_args2mutable_pod_req
                    request = peas_args2mutable_pod_req(p.peas_args)
                elif _req_type == jina_pb2.SpawnRequest.MutablepodSpawnRequest:
                    from .remote import mutable_pod_req2peas_args
                    p = Pod(mutable_pod_req2peas_args(_req), allow_remote=False)
                else:
                    raise BadRequestType('don\'t know how to handle %r' % _req_type)

                with p:
                    self.peapods.append(p)
                    for l in p.log_iterator:
                        request.log_record = l.msg
                        yield request
                self.peapods.remove(p)
            else:
                warn_msg = f'the gateway at {self.args.host}:{self.args.port_grpc} ' \
                           f'does not support remote spawn, please restart it with --allow-spawn'
                request.log_record = warn_msg
                request.status = jina_pb2.SpawnRequest.ERROR_NOTALLOWED
                self.logger.warning(warn_msg)
                for j in range(1):
                    yield request

        def close(self):
            for p in self.peapods:
                p.close()
