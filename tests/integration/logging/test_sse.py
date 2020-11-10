import os
import time
import threading

import yaml
from jina.logging.sse import start_sse_logger

cur_dir = os.path.dirname(os.path.abspath(__file__))
GROUP_ID = 'flow_id'
LOG_MESSAGE = 'log message'


def feed_path_logs(path, threading_event):
    while True:
        os.makedirs(path, exist_ok=True)
        file = os.path.join(path, 'log.log')
        if not threading_event.is_set():
            with open(file, 'a') as fp:
                fp.write(LOG_MESSAGE)
                fp.flush()
                time.sleep(0.1)
        else:
            break


def sse_client(wrap):
    from sseclient import SSEClient
    def with_requests(url):
        """Get a streaming response for the given event feed using requests."""
        import requests
        return requests.get(url, stream=True)

    url = 'http://0.0.0.0:5000/stream/log'
    response = with_requests(url)
    client = SSEClient(response)
    events = client.events()
    event = next(events)
    if LOG_MESSAGE not in event.data:
        wrap.add()


def stop_log_server():
    import urllib.request
    urllib.request.urlopen('http://0.0.0.0:5000/action/shutdown', timeout=5)


def test_sse_client(tmpdir):
    class WrapAssert:
        def __init__(self):
            self.count = 0

        def add(self):
            self.count += 1

    conf_path = os.path.join(tmpdir, 'log')
    path = os.path.join(conf_path, GROUP_ID)
    event = threading.Event()

    feed_thread = threading.Thread(name='feed_path_logs',
                                   target=feed_path_logs, daemon=False,
                                   kwargs={'path': path, 'threading_event': event})

    with open(os.path.join(cur_dir, 'logserver_config.yml')) as fp:
        log_config = yaml.load(fp)

    log_config['files']['log'] = conf_path

    sse_server_thread = threading.Thread(name='sentinel-sse-logger',
                                         target=start_sse_logger, daemon=False,
                                         args=(log_config,
                                               GROUP_ID,
                                               None))

    wrap = WrapAssert()
    sse_client_thread = threading.Thread(name='sse-client',
                                         target=sse_client,
                                         daemon=False,
                                         kwargs=({'wrap': wrap}))

    feed_thread.start()
    time.sleep(0.5)
    sse_server_thread.start()
    time.sleep(0.5)
    sse_client_thread.start()
    time.sleep(0.5)
    event.set()
    stop_log_server()
    feed_thread.join()
    sse_server_thread.join()
    sse_client_thread.join()

    assert wrap.count > 0
