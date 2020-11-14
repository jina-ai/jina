__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time
from typing import Optional, Dict

from . import default_logger
from .. import JINA_GLOBAL, __version__
from ..importer import ImportExtensions


def start_sse_logger(log_config: Dict,
                     log_id: str,
                     flow_yaml: Optional[str] = None):
    """Start a logger that emits server-side event from the log queue, so that one can use a browser to monitor the logs

    :param log_config: configuration of the sse server
    :param log_id: log-id of `Flow`
    :param flow_yaml: Flow yaml description

    Example:

    .. highlight:: javascript
    .. code-block:: javascript

        var stream = new EventSource('http://localhost:5000/log/stream');
        stream.onmessage = function (e) {
            console.info(e.data);
        };
        stream.onerror = function (err) {
            console.error("EventSource failed:", err);
            stream.close()
        };

    """
    with ImportExtensions(required=True):
        from flask import Flask, Response, jsonify
        from flask_cors import CORS
        from gevent.pywsgi import WSGIServer
        import gevent

    JINA_GLOBAL.logserver.address = f'http://{log_config["host"]}:{log_config["port"]}'

    JINA_GLOBAL.logserver.ready = JINA_GLOBAL.logserver.address + \
                                  log_config['endpoints']['ready']
    JINA_GLOBAL.logserver.shutdown = JINA_GLOBAL.logserver.address + \
                                     log_config['endpoints']['shutdown']

    app = Flask(__name__)
    CORS(app)
    server = WSGIServer((log_config['host'], log_config['port']), app, log=None)

    def _log_stream(path):
        import glob
        # fluentd creates files under this path with some tag based on day, so as temp solution,
        # just get the first file matching this patter once it appears
        file = f'{path}/{log_id}/log.log'
        with open(file) as fp:
            fp.seek(0, 2)
            while True:
                readline = fp.readline()
                line = readline.strip()
                if line:
                    yield f'data: {line}\n\n'
                else:
                    time.sleep(0.1)

    @app.route(log_config['endpoints']['log'])
    def get_log():
        """Get the logs, endpoint `/log/stream`  """
        return Response(_log_stream(log_config['files']['log']), mimetype="text/event-stream")

    @app.route(log_config['endpoints']['yaml'])
    def get_yaml():
        """Get the yaml of the flow  """
        return flow_yaml

    @app.route(log_config['endpoints']['profile'])
    def get_profile():
        """Get the profile logs, endpoint `/profile/stream`  """
        return Response(_log_stream(log_config['files']['profile']), mimetype='text/event-stream')

    @app.route(log_config['endpoints']['podapi'])
    def get_podargs():
        """Get the default args of a pod"""

        from ..parser import set_pod_parser
        from argparse import _StoreAction, _StoreTrueAction
        port_attr = ('help', 'choices', 'default')
        d = {}
        parser = set_pod_parser()
        for a in parser._actions:
            if isinstance(a, _StoreAction) or isinstance(a, _StoreTrueAction):
                d[a.dest] = {p: getattr(a, p) for p in port_attr}
                if a.type:
                    d[a.dest]['type'] = a.type.__name__
                elif isinstance(a, _StoreTrueAction):
                    d[a.dest]['type'] = 'bool'
                else:
                    d[a.dest]['type'] = a.type

        d = {'pod': d, 'version': __version__, 'usage': parser.format_help()}
        return jsonify(d)

    @app.route(log_config['endpoints']['shutdown'])
    def shutdown():
        server.stop()
        return 'Server shutting down...'

    @app.route(log_config['endpoints']['ready'])
    def is_ready():
        return Response(status=200)

    try:
        server.serve_forever()
        gevent.get_hub().join()
    except Exception as ex:
        default_logger.error(ex)
