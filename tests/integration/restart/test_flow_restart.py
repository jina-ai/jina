import os
import threading
import time
import shutil
import contextlib
import pytest

from jina import Flow, Client, DocumentArray, Executor, requests
from jina.helper import random_port


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


class MyExecutorBeforeRestart(Executor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorBeforeRestart'


class MyExecutorAfterRestart(Executor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorAfterRestart'


@pytest.fixture
def flow_yamls(tmpdir):
    port = random_port()
    f1 = Flow(restart=True, port=port).add(uses=MyExecutorBeforeRestart)
    f1.build()
    f1.save_config(os.path.join(str(tmpdir), 'flow.yml'))
    f2 = Flow(port=port).add(uses=MyExecutorAfterRestart)
    f2.build()
    f2.save_config(os.path.join(str(tmpdir), 'flow_new.yml'))


def test_flow_restart(flow_yamls, tmpdir):
    stop_event = threading.Event()

    flow = Flow.load_config(os.path.join(str(tmpdir), 'flow.yml'))
    t = threading.Thread(target=flow_run, args=(flow, stop_event))
    t.start()
    time.sleep(5)
    try:
        client = Client(port=flow.port, protocol=str(flow.protocol))
        res = client.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeRestart'
        with _update_file(os.path.join(str(tmpdir), 'flow_new.yml'), os.path.join(str(tmpdir), 'flow.yml'), str(tmpdir)):
            client = Client(port=flow.port, protocol=str(flow.protocol))
            res = client.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterRestart'
        client = Client(port=flow.port, protocol=str(flow.protocol))
        res = client.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeRestart'
    finally:
        stop_event.set()
        t.join()
