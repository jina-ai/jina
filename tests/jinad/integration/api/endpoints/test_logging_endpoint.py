import json
import pathlib
import random
import time
import uuid
from datetime import datetime, timezone
from multiprocessing import Process, Event

import pytest

from daemon.config import log_config
from daemon.excepts import NoSuchFileException

LOG_MESSAGE = 'log message'
TIMEOUT_ERROR_CODE = 4000


def feed_path_logs(filepath, total_lines, sleep, mp_event=None):
    # method to write logs to a file in random interval
    # this runs in a separate thread
    pathlib.Path(filepath).parent.absolute().mkdir(parents=True, exist_ok=True)
    with open(filepath, 'a', buffering=1) as fp:
        for i in range(total_lines):
            message = f'{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")}\t' \
                      f'jina\t' \
                      f'{{"host": "blah", "process": "blah", "message": "{LOG_MESSAGE} {i+1}" }}'
            fp.writelines(message + '\n')
            time.sleep(sleep)
    if mp_event:
        mp_event.set()


@pytest.mark.asyncio
async def test_logging_endpoint_invalid_id(fastapi_client):
    log_id = uuid.uuid1()
    with pytest.raises(NoSuchFileException):
        with fastapi_client.websocket_connect(f'logstream/{log_id}'):
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, sleep', [
    (10, 0.5),
    (20, random.random())
])
async def test_logging_dashboard(fastapi_client, total_lines, sleep):
    """
    This test verifies the use case when dashboard would stream log lines

    We have a process running in the background writing logs every `sleep` seconds (sleep < 1sec)
    Websocket client
        - connects to the stream with a timeout of 1 secs (set by query param `timeout`)
        - sends a single json message {'from': 0}
        - waits & processes a stream of messages from the server.
        - client doesn't need to respond back to every message.
        - server sends a {'code': `TIMEOUT_ERROR_CODE`} when it cannot read any messages in last `timeout` secs
        - client can either break out of the loop & ask for the next set of log lines
    """
    log_id = uuid.uuid1()
    filepath = log_config.PATH % log_id

    Process(target=feed_path_logs,
            args=(filepath, total_lines, sleep,),
            daemon=True).start()
    # sleeping for 2 secs to allow the process to write logs
    time.sleep(2)

    with fastapi_client.websocket_connect(f'logstream/{log_id}?timeout=1') as websocket:
        websocket.send_json({'from': 0})
        while True:
            data = websocket.receive_json()
            if 'code' in data:
                assert data['code'] == TIMEOUT_ERROR_CODE
                print('Got timeout error code. Breaking')
                break
            assert len(data) == 1
            current_line_number = list(data.keys())[0]
            complete_log_line = data[current_line_number]
            current_log_message = json.loads(complete_log_line.split('\t')[-1].strip())
            print(f'Current line#: {current_line_number}, Resonse: {current_log_message}')
            assert current_log_message['message'] == LOG_MESSAGE + ' ' + current_line_number


@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, sleep, timeout', [
    (10, random.random(), 1),
    (10, random.uniform(0.8, 1.5), 1),
    (10, random.uniform(1.2, 1.5), 1),
])
async def test_logging_core(fastapi_client, total_lines, sleep, timeout):
    """
    This test verifies the use case when Flow creates a remote Pod & streams the logs

    We have a process running in the background writing logs every `sleep` seconds.
    Once the logs are written, it sets a `multiprocessing.Event()`.
    The Event is set by `cancel()` in `JinadRuntime`.

    Websocket client
        - connects to the stream with a timeout of `timeout` secs (set by query param `timeout`)
        - There are 2 loops in play here.
        - Outer loop starts by sending a single json message {'from': 0}
        - Inner loop waits & processes a stream of messages from the server.
        - Whenever server sends a {'code': `TIMEOUT_ERROR_CODE`}, it breaks out of the inner loop.
        - (This means, there were no logs seen by the server in last `timeout` seconds)
        - Outer loop asks for the next set of logs {'from': current_line + 1}, if the `Event` is set
        - Outer loop exits out, if event is set

    Test parameters:
        - `sleep` < `timeout`
        - `sleep` ~ `timeout`
        - `sleep` > `timeout`
    """

    log_id = uuid.uuid1()
    filepath = log_config.PATH % log_id
    event = Event()

    Process(target=feed_path_logs,
            args=(filepath, total_lines, sleep, event, ),
            daemon=True).start()
    # sleeping for 2 secs to allow the process to write logs
    time.sleep(2)

    with fastapi_client.websocket_connect(f'logstream/{log_id}?timeout={timeout}') as websocket:
        current_line_number = -1
        # During tests, these are usual function calls not awaitables
        # https://www.starlette.io/testclient/#testing-websocket-sessions

        while not event.is_set():
            print(f'\nAsking to fetch logs from line # {int(current_line_number) + 1}')
            websocket.send_json({'from': int(current_line_number) + 1})
            while True:
                data = websocket.receive_json()
                if 'code' in data:
                    assert data['code'] == TIMEOUT_ERROR_CODE
                    print('Got timeout error code. Breaking')
                    break
                assert len(data) == 1
                current_line_number = list(data.keys())[0]
                complete_log_line = data[current_line_number]
                current_log_message = json.loads(complete_log_line.split('\t')[-1].strip())
                print(f'Current line#: {current_line_number}, Resonse: {current_log_message}')
                assert current_log_message['message'] == LOG_MESSAGE + ' ' + current_line_number

    print('Client disconnected')

    pathlib.Path(filepath).unlink()


@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, sleep, disconnect_line_num', [
    (10, 0.5, 4),
    (20, random.random(), 9)
])
async def test_logging_client_disconnection(fastapi_client, total_lines, sleep, disconnect_line_num):
    """
    This test verifies the use case when a client disconnects in the middle of streaming,
    and there's no exception raised by the server.
    """
    log_id = uuid.uuid1()
    filepath = log_config.PATH % log_id

    Process(target=feed_path_logs,
            args=(filepath, total_lines, sleep,),
            daemon=True).start()
    # sleeping for 2 secs to allow the process to write logs
    time.sleep(2)

    with fastapi_client.websocket_connect(f'logstream/{log_id}?timeout=1') as websocket:
        websocket.send_json({'from': 0})
        while True:
            data = websocket.receive_json()
            if 'code' in data:
                assert data['code'] == TIMEOUT_ERROR_CODE
                print('Got timeout error code. Breaking')
                break
            assert len(data) == 1
            current_line_number = list(data.keys())[0]
            complete_log_line = data[current_line_number]
            current_log_message = json.loads(complete_log_line.split('\t')[-1].strip())
            print(f'Current line#: {current_line_number}, Resonse: {current_log_message}')
            assert current_log_message['message'] == LOG_MESSAGE + ' ' + current_line_number
            if int(current_line_number) == disconnect_line_num:
                break
