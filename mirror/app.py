from http.server import BaseHTTPRequestHandler, HTTPServer
from opentelemetry.proto.trace.v1 import trace_pb2
from opentelemetry.proto.metrics.v1 import metrics_pb2
import logging
import os
from pathlib import Path

METRIC_STORE = Path('./metrics')
TRACE_STORE = Path('./traces')
OTHER_STORE = Path('./other')

def init_storage():
    """Initialize metrics and traces storage directories."""
    logging.info('Initializing storage...')
    for i in [METRIC_STORE, TRACE_STORE, OTHER_STORE]:
        i.mkdir(exist_ok=True)
        with open(i / 'counter', 'w') as f:
            f.write('0')
    logging.info(f'Storage Initialized\nMetrics: {METRIC_STORE}\nTraces: {TRACE_STORE}')

def write(dir: Path, data: bytes):
    """Write data to a file in the given directory.
    
    Args:
        dir (Path): The directory to write to.
        data (bytes): The data to write.
    """
    with open(dir / 'counter', 'r') as f:
        counter = int(f.read())
    with open(dir / f'{counter}', 'wb') as f:
        f.write(data)
    with open(dir / 'counter', 'w') as f:
        f.write(str(counter + 1))

def read(dir: Path, req_path: str) -> bytes:
    """Read data from a directory.
    
    Args:
        dir (Path): The directory to read from.
        req_path (str): The path of the request.
    """
    relative_path = req_path.split('/')[-1]
    with open(dir / relative_path, 'rb') as f:
        return f.read()

class OtelStoringRequestHandler(BaseHTTPRequestHandler):
    """HTTP Server that stores traces and metrics."""
    def do_GET(self):
        logging.info(f"GET {self.path}\n{self.headers}\n")

        resp_status: int = 200
        resp_content_type: str = 'text/html'
        resp_content: bytes = None

        if self.path.startswith('/v1/traces'):
            resp_content = read(TRACE_STORE, self.path)
            resp_content_type = 'application/x-protobuf'
        elif self.path.startswith('/v1/metrics'):
            resp_content = read(METRIC_STORE, self.path)
            resp_content_type = 'application/x-protobuf'
        elif self.path.startswith('/v1/other'):
            resp_content = read(OTHER_STORE, self.path)
            resp_content_type = 'application/x-protobuf'
        elif self.path == '/health':
            resp_content = "OK".encode('utf-8')
        elif self.path == '/ping':
            resp_content = "pong".encode('utf-8')
        else:
            resp_status = 404
            resp_content = "Not Found.".encode('utf-8')

        self.send_response(resp_status)
        self.send_header('Content-type', resp_content_type)
        self.end_headers()
        self.wfile.write(resp_content)

    def do_POST(self):
        logging.info(f"POST {self.path}\n{self.headers}\n")

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        if self.path == '/v1/traces':
            write(TRACE_STORE, post_data)
        elif self.path == '/v1/metrics':
            write(METRIC_STORE, post_data)
        else:
            write(OTHER_STORE, post_data)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Job Done.".encode('utf-8'))

def run(handler_class: BaseHTTPRequestHandler, port: int=8000):
    """Run the server.
    
    Args:
        handler_class (BaseHTTPRequestHandler): The BaseHTTPRequestHandler class to use.
        port (int): The port to listen on.
    """

    init_storage()
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    # Set logging level
    if 'MEOW_LOGLEVEL' in os.environ:
        logging.basicConfig(level=os.environ['MEOW_LOGLEVEL'])
    else:
        logging.basicConfig(level=logging.INFO)

    # Set port
    if 'MEOW_PORT' in os.environ:
        port = int(os.environ['MEOW_PORT'])
    else:
        port = 8000

    run(OtelStoringRequestHandler, port=port)
