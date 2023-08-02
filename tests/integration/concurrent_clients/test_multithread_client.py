import threading
import time
from concurrent.futures import ThreadPoolExecutor

from jina import Client, Document, Executor, Flow, requests
from jina.helper import random_port


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from MyExecutor'


def flow_run(flow, stop_event):
    with flow:
        flow.block(stop_event)


def client_post(doc, port, client):
    result = client.post(on='/', inputs=doc)[0]
    print(f'doc.id {doc.id} vs result.id {result.id}')
    return result


def test_multithread_client(capsys):
    port = random_port()
    stop_event = threading.Event()
    flow = Flow(port=port).add(uses=MyExecutor)
    t = threading.Thread(target=flow_run, args=(flow, stop_event))

    c = Client(port=port)

    try:
        with capsys.disabled():
            t.start()
            time.sleep(5)

        with ThreadPoolExecutor(max_workers=50) as pool:
            tasks = []
            for i in range(1000):
                doc = Document(id=f'{i}', text='hello world')
                task = pool.submit(client_post, doc, port, c)
                tasks.append(task)

            for i, task in enumerate(tasks):
                result = task.result()
                assert result.id == f'{i}'
                assert result.text == 'I am coming from MyExecutor'

        with capsys.disabled():
            stdout, stderr = capsys.readouterr()
            assert 'BlockingIOError' not in stderr

    finally:
        stop_event.set()
        t.join()
