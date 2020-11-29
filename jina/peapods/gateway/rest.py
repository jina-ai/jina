import asyncio

from google.protobuf.json_format import MessageToJson

from .grpc import GRPCServicer
from ..pea import BasePea
from ...enums import RequestType
from ...importer import ImportExtensions


class RESTGatewayPea(BasePea):
    """A :class:`BasePea`-like class for holding a HTTP Gateway.

    :class`RESTGatewayPea` is still in beta. Feature such as prefetch is not available yet.
    Unlike :class:`GatewayPea`, it does not support bi-directional streaming. Therefore, it is
    synchronous from the client perspective.
    """

    # TODO: move this to AsyncCtrlZmqlet based termination

    def loop_body(self):
        self._p_servicer = GRPCServicer(self.args)
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
            from ...clients import python
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
