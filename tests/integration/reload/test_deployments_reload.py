import contextlib
import os
import shutil
import threading
import time

import pytest

from jina import Client, DocumentArray, Executor, Flow, requests
from jina.helper import random_port

cur_dir = os.path.dirname(__file__)


@contextlib.contextmanager
def _update_file(input_file_path, output_file_path, temp_path):
    backup_file = os.path.join(temp_path, 'backup.yaml')
    try:
        shutil.copy2(output_file_path, backup_file)
        shutil.copy(input_file_path, output_file_path)
        time.sleep(2.0)
        yield
    finally:
        shutil.copy2(backup_file, output_file_path)
        time.sleep(5.0)


def flow_run(flow, stop_event):
    with flow:
        flow.block(stop_event)


def test_deployment_reload(tmpdir):
    stop_event = threading.Event()

    flow = Flow().add(
        uses=os.path.join(os.path.join(cur_dir, 'exec'), 'config.yml'), reload=True
    )
    t = threading.Thread(target=flow_run, args=(flow, stop_event))
    t.start()
    time.sleep(5)
    try:
        client = Client(port=flow.port, protocol=str(flow.protocol))
        res = client.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
        with _update_file(
            os.path.join(os.path.join(cur_dir, 'exec'), 'config_alt.yml'),
            os.path.join(os.path.join(cur_dir, 'exec'), 'config.yml'),
            str(tmpdir),
        ):
            client = Client(port=flow.port, protocol=str(flow.protocol))
            res = client.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterReload'
        client = Client(port=flow.port, protocol=str(flow.protocol))
        res = client.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
    finally:
        stop_event.set()
        t.join()
