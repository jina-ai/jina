__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
import os
import threading

import grpc
from google.protobuf.json_format import MessageToJson

from .grpc_asyncio import AsyncioExecutor
from .pea import BasePea
from .zmq import AsyncZmqlet, AsyncCtrlZmqlet, send_message_async, recv_message_async, send_ctrl_message
from .. import __stop_msg__, Request
from ..enums import RequestType
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

        def handle(self, msg: 'Message') -> 'Request':
            msg.add_route(self.name, self.args.identity)
            return msg.response

        async def CallUnary(self, request, context):
            with AsyncZmqlet(self.args, logger=self.logger) as zmqlet:
                await zmqlet.send_message(Message(None, request, 'gateway',
                                                  **vars(self.args)))
                return await zmqlet.recv_message(callback=self.handle)

        async def Call(self, request_iterator, context):
            print('#################################')
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


class AsyncGatewayPea:
    def __init__(self, args):
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

        self.logger = JinaLogger(context=self.__class__.__name__,
                                 name='gateway',
                                 log_id=args.log_id,
                                 log_config=args.log_config)
        self._p_servicer = GatewayPea._Pea(args)
        self.configure_event_loop()
        self.is_gateway_ready = asyncio.Event()
        self.init_server(args)

    def configure_event_loop(self):
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
        self.logger.info('IN AsyncGatewayPea start()')
        await self._server.start()
        self.logger.success(f'gateway is listening at: {self._bind_address}')
        await self.is_gateway_ready.wait()
        return self

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._server.stop(None)
        self.logger.close()


class _GatewayPea(BasePea):
    def __init__(self, args):
        super().__init__(args)
        self.logger.info('In __init__')
        if not args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self._p_servicer = GatewayPea._Pea(args)
        self.ctrl_addr, _ = AsyncCtrlZmqlet.get_ipc_ctrl_address()
        self.logger.warning(f'name: {self.name}, ctrl_addr: {self.ctrl_addr}')

    async def handle_terminate_signal(self):
        from ..types.message.common import ControlMessage
        with AsyncCtrlZmqlet(args=self.args, logger=self.logger, ctrl_addr=self.ctrl_addr) as zmqlet:
            # TODO: currently exits for any ctrl message. should only happen for terminate
            msg = await recv_message_async(sock=zmqlet.ctrl_sock)
            # TODO: send_message_async needs to send a message of type `Message`, can be avoided?
            await send_message_async(sock=zmqlet.ctrl_sock, msg=ControlMessage('STATUS'))
            self.loop_teardown()
            self.is_shutdown.set()

    async def _loop_body(self):
        self.gateway_task = asyncio.get_event_loop().create_task(self.gateway.start())
        # we cannot use zmqstreamlet here, as that depends on a custom loop
        self.zmq_task = asyncio.get_running_loop().create_task(self.handle_terminate_signal())
        # gateway gets started without awaiting the task, as we don't want to suspend the loop_body here
        # event loop should be suspended depending on zmq ctrl recv, hence awaiting here
        try:
            await self.zmq_task
        except asyncio.CancelledError:
            self.logger.info('zmq_task got cancelled')

    def loop_body(self):
        self.gateway = AsyncGatewayPea(self.args)
        self.set_ready()
        # asyncio.run() or asyncio.run_until_complete() wouldn't work here as we are running a custom loop
        asyncio.get_event_loop().run_until_complete(self._loop_body())

    async def _loop_teardown(self):
        # TODO: This might not be required, as setting the asyncio Event stops the server
        await asyncio.get_event_loop().create_task(self.gateway.stop())

    def loop_teardown(self):
        self.zmq_task.cancel()
        if hasattr(self, 'gateway'):
            self.gateway.is_gateway_ready.set()
            # asyncio.get_event_loop().run_until_complete(self._loop_teardown())

    def send_terminate_signal(self):
        if self.is_ready_event.is_set() and hasattr(self, 'ctrl_addr'):
            # TODO: set a timeout in the args, rather than using fixed number?
            send_ctrl_message(self.ctrl_addr, 'TERMINATE',
                              timeout=10000)

    def close(self) -> None:
        self.send_terminate_signal()
        self.is_shutdown.wait()
        self.logger.success(__stop_msg__)
        self.logger.close()
        if not self.daemon:
            self.join()


class RESTGatewayPea(BasePea):
    """A :class:`BasePea`-like class for holding a HTTP Gateway.

    :class`RESTGatewayPea` is still in beta. Feature such as prefetch is not available yet.
    Unlike :class:`GatewayPea`, it does not support bi-directional streaming. Therefore, it is
    synchronous from the client perspective.
    """
    # TODO: move this to AsyncCtrlZmqlet based termination

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

            content['mode'] = RequestType.from_string(mode)

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
