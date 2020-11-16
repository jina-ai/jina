__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
import os
import threading

import grpc
from google.protobuf.json_format import MessageToJson

from .grpc_asyncio import AsyncioExecutor
from .pea import BasePea
from .zmq import AsyncZmqlet
from .. import __stop_msg__
from ..enums import ClientMode
from ..helper import use_uvloop
from ..importer import ImportExtensions
from ..logging import JinaLogger
from ..logging.profile import TimeContext
from ..proto import jina_pb2_grpc, jina_pb2
from jina.types.message import Message

use_uvloop()


class GatewayPea:
    """A :class:`BasePea`-like class for holding a gRPC Gateway.

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

        self.logger = JinaLogger(context=self.__class__.__name__,
                                 name='gateway',
                                 log_id=args.log_id,
                                 log_config=args.log_config)
        self._p_servicer = self._Pea(args)
        self._stop_event = threading.Event()
        self.is_ready = threading.Event()
        self.init_server(args)

    def init_server(self, args):
        self._ae = AsyncioExecutor()
        self._server = grpc.server(
            self._ae,
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self._p_servicer, self._server)
        self._bind_address = f'{args.host}:{args.port_expose}'
        self._server.add_insecure_port(self._bind_address)

    def __enter__(self):
        return self.start()

    def start(self):
        self._server.start()
        self.logger.success(f'gateway is listening at: {self._bind_address}')
        self._stop_event.clear()
        self.is_ready.set()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._ae.shutdown()
        self._server.stop(None)
        self._stop_event.set()
        self.logger.success(__stop_msg__)
        self.logger.close()

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
            self.logger = JinaLogger(self.name, **vars(args))

        def handle(self, msg: 'Message') -> 'jina_pb2.RequestProto':
            """ Note gRPC accepts :class:`jina_pb2.RequestProto` only, so no more :class:`Request`.

            :param msg:
            :return:
            """
            msg.add_route(self.name, self.args.identity)
            return msg.response

        async def CallUnary(self, request, context):
            with AsyncZmqlet(self.args, logger=self.logger) as zmqlet:
                await zmqlet.send_message(Message(None, request, 'gateway',
                                                  **vars(self.args)))
                return await zmqlet.recv_message(callback=self.handle)

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
                                    Message(None, next(request_iterator), 'gateway',
                                            **vars(self.args))))
                            fetch_to.append(asyncio.create_task(zmqlet.recv_message(callback=self.handle)))
                        except StopIteration:
                            return True
                    return False

                with TimeContext(f'prefetching {self.args.prefetch} requests', self.logger):
                    self.logger.warning('if this takes too long, you may want to take smaller "--prefetch" or '
                                        'ask client to reduce "--batch-size"')
                    is_req_empty = prefetch_req(self.args.prefetch, prefetch_task)
                    if is_req_empty and not prefetch_task:
                        self.logger.error('receive an empty stream from the client! '
                                          'please check your client\'s input_fn, '
                                          'you can use "PyClient.check_input(input_fn())"')
                        return

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


class RESTGatewayPea(BasePea):
    """A :class:`BasePea`-like class for holding a HTTP Gateway.

    :class`RESTGatewayPea` is still in beta. Feature such as prefetch is not available yet.
    Unlike :class:`GatewayPea`, it does not support bi-directional streaming. Therefore, it is
    synchronous from the client perspective.
    """

    def loop_body(self):
        self._p_servicer = GatewayPea._Pea(self.args)
        self.get_http_server()

    def close(self):
        if hasattr(self, 'terminate'):
            self.terminate()
        self.logger.close()

    def get_http_server(self):
        with ImportExtensions(required=True):
            from flask import Flask, Response, jsonify, request
            from flask_cors import CORS, cross_origin
            from gevent.pywsgi import WSGIServer

        app = Flask(__name__)
        app.config['CORS_HEADERS'] = 'Content-Type'
        CORS(app)

        def http_error(reason, code):
            return jsonify({'reason': reason}), code

        @app.route('/ready')
        @cross_origin()
        def is_ready():
            return Response(status=200)

        @app.route('/api/<mode>', methods=['POST'])
        @cross_origin()
        def api(mode):
            from ..clients import python
            mode_fn = getattr(python.request, mode, None)
            if mode_fn is None:
                return http_error(f'mode: {mode} is not supported yet', 405)
            content = request.json
            if 'data' not in content:
                return http_error('"data" field is empty', 406)

            content['mode'] = ClientMode.from_string(mode)

            results = get_result_in_json(getattr(python.request, mode)(**content))
            return Response(asyncio.run(results),
                            status=200,
                            mimetype='application/json')

        async def get_result_in_json(req_iter):
            return [MessageToJson(k) async for k in self._p_servicer.Call(req_iter, None)]

        # os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        # log = logging.getLogger('werkzeug')
        # log.disabled = True
        # app.logger.disabled = True

        # app.run('0.0.0.0', 5000)
        server = WSGIServer((self.args.host, self.args.port_expose), app, log=None)

        def close(*args, **kwargs):
            server.stop()
            self.unset_ready()
            self.is_shutdown.set()

        from gevent import signal
        signal.signal(signal.SIGTERM, close)
        signal.signal(signal.SIGINT, close)  # CTRL C
        self.set_ready()
        self.logger.warning('you are using a REST gateway, which is still in early beta version. '
                            'advanced features such as prefetch and streaming are disabled.')
        server.serve_forever()
