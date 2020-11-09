__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
from typing import Optional, List

from . import default_logger
from .. import JINA_GLOBAL, __version__
from ..helper import yaml


def start_sse_logger(server_config_path: str, identity: str, pod_identities: List[str], flow_yaml: Optional[str] = None):
    """Start a logger that emits server-side event from the log queue, so that one can use a browser to monitor the logs

    :param server_config_path: Path to the server configuration file path
    :param identity: identifies of `Flow`
    :param pod_identities: the identities of the Pods context managed by the Flow
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
    try:
        from flask import Flask, Response, jsonify
        from flask_cors import CORS
        from gevent.pywsgi import WSGIServer
        import gevent
    except ImportError:
        raise ImportError('Flask or its dependencies are not fully installed, '
                          'they are required for serving HTTP requests.'
                          'Please use pip install "jina[http]" to install it.')

    try:
        with open(server_config_path) as fp:
            _config = yaml.load(fp)
    except Exception as ex:
        default_logger.error(ex)
    JINA_GLOBAL.logserver.address = f'http://{_config["host"]}:{_config["port"]}'

    JINA_GLOBAL.logserver.ready = JINA_GLOBAL.logserver.address + \
                                  _config['endpoints']['ready']
    JINA_GLOBAL.logserver.shutdown = JINA_GLOBAL.logserver.address + \
                                     _config['endpoints']['shutdown']

    app = Flask(__name__)
    CORS(app)
    server = WSGIServer((_config['host'], _config['port']), app, log=None)

    def _log_stream(base_path):
        loop = asyncio.get_event_loop()
        lines = []
        async def gather_lines_from_file(path):
            import glob
            # fluentd creates files under this path with some tag based on day, so as temp solution,
            # just get the first file matching this patter once it appears
            while len(glob.glob(f'{path}/log.log')) == 0:
                await asyncio.sleep(0.1)

            file = glob.glob(f'{path}/log.log')[0]
            with open(file) as fp:
                fp.seek(0, 2)
                while True:
                    line = fp.readline().strip()
                    if line:
                        lines.append(f'data: {line}\n\n')
                    else:
                        await asyncio.sleep(0.1)

        async def send_all():
            while True:
                if not lines:
                    await asyncio.sleep(0.1)
                else:
                    yield lines.pop()
        identities = pod_identities
        identities.extend(identity)
        log_paths = list(map(lambda x: f'{base_path}/{x}', identities))
        [loop.create_task(gather_lines_from_file(path)) for path in log_paths]
        loop.create_task(send_all)
        loop.run_forever()

    @app.route(_config['endpoints']['log'])
    def get_log():
        """Get the logs, endpoint `/log/stream`  """
        return Response(_log_stream(_config['files']['log']), mimetype="text/event-stream")

    @app.route(_config['endpoints']['yaml'])
    def get_yaml():
        """Get the yaml of the flow  """
        return flow_yaml

    @app.route(_config['endpoints']['profile'])
    def get_profile():
        """Get the profile logs, endpoint `/profile/stream`  """
        return Response(_log_stream(_config['files']['profile']), mimetype='text/event-stream')

    @app.route(_config['endpoints']['podapi'])
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

    @app.route(_config['endpoints']['shutdown'])
    def shutdown():
        server.stop()
        return 'Server shutting down...'

    @app.route(_config['endpoints']['ready'])
    def is_ready():
        return Response(status=200)

    try:
        server.serve_forever()
        gevent.get_hub().join()
    except Exception as ex:
        default_logger.error(ex)
