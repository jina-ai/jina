import logging

from .queue import __sse_queue__, __profile_queue__


def start_sse_logger(host: str, port: int):
    """Start a logger that emits server-side event from the log queue, so that one can use a browser to monitor the logs

    :param host: host address of the server
    :param port: port of the server

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
        from flask import Flask, Response
        from flask_cors import CORS
    except ImportError:
        raise ImportError('Flask or its dependencies are not fully installed, '
                          'they are required for serving HTTP requests.'
                          'Please use "pip install jina[flask]" to install it.')

    app = Flask(__name__)
    CORS(app)

    @app.route('/stream/log')
    def get_log():
        """Get the logs, endpoint `/log/stream`  """
        return Response(_log_stream(), mimetype="text/event-stream")

    @app.route('/stream/profile')
    def get_profile():
        """Get the profile logs, endpoint `/profile/stream`  """
        return Response(_profile_stream(), mimetype="text/event-stream")

    @app.route('/shutdown')
    def shutdown():
        from flask import request
        if not 'werkzeug.server.shutdown' in request.environ:
            raise RuntimeError('Not running the development server')
        request.environ['werkzeug.server.shutdown']()
        return 'Server shutting down...'

    @app.route('/is_ready')
    def is_ready():
        return Response(status=200)

    # os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    log = logging.getLogger('werkzeug')
    log.disabled = True
    app.logger.disabled = True
    app.run(port=port, host=host)


def _log_stream():
    while True:
        try:
            message = __sse_queue__.get()
            yield 'data: {}\n\n'.format(message.msg)
        except EOFError:
            yield 'LOG ENDS\n\n'
            break


def _profile_stream():
    while True:
        try:
            message = __profile_queue__.get()
            yield 'data: {}\n\n'.format(message.msg)
        except EOFError:
            yield 'PROFILE ENDS\n\n'
            break
