
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from jina import Client, Document, Executor, Flow, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from MyExecutor'
                
def flow_run(flow, stop_event):
    with flow:
        flow.block(stop_event)


def client_post(c):
    doc = Document(id='doc', text='hello world')
    result = c.post(on='/', inputs=doc)[0]
    return result


def test_multithread_client(capsys):
    stop_event = threading.Event()
    flow = Flow(port=12345).add(uses=MyExecutor)
    t = threading.Thread(target=flow_run, args=(flow, stop_event))

    c = Client(port=12345)

    try:
        with capsys.disabled():
            t.start()
            time.sleep(5)

        with ThreadPoolExecutor(max_workers=50) as pool:
            tasks = []
            for _ in range(1000):
                task = pool.submit(client_post, c)
                tasks.append(task)

            for task in tasks:
                result = task.result()
                assert result.id == 'doc'
                assert result.text == 'I am coming from MyExecutor'

        with capsys.disabled():
            stdout, stderr = capsys.readouterr()
            assert 'BlockingIOError' not in stderr

    finally:
        stop_event.set()
        t.join()
