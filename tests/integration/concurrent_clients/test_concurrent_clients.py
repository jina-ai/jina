import pytest

from jina import Flow, Executor, requests, DocumentArray, Document
from jina.types.request import Response
import threading, queue
import random
import time
from functools import partial
from jina import Client, Document


class MyExecutor(Executor):
    @requests(on='/ping')
    def ping(self, docs: DocumentArray, **kwargs):
        time.sleep(3 * random.random())


@pytest.mark.parametrize('protocal', ['http', 'grpc'])
@pytest.mark.parametrize('parallel', [10])
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
@pytest.mark.parametrize('prefetch', [10])
@pytest.mark.parametrize('concurrent', [25])
def test_concurrent_clients(concurrent, protocal, parallel, polling, prefetch):
    # def pong(peer_hash, resp: Response):
    #     for d in resp.docs:
    #         print(f'{d.text} vs {peer_hash}')
    #         assert d.text == peer_hash

    tasks = queue.Queue()

    def peer_client(port, protocal, peer_hash):
        c = Client(protocol=protocal, port_expose=port)
        for _ in range(10):
            tasks.put(peer_hash)
            resps = c.post('/ping', Document(text=peer_hash), return_results=True)
            for r in resps:
                for d in r.docs:
                    if d.text != peer_hash:
                        return
            tasks.task_done()

    thread_pool = []
    for peer_id in range(concurrent):
        t = threading.Thread(
            target=partial(peer_client, '12345', protocal, str(peer_id)), daemon=True
        )
        thread_pool.append(t)

    f = Flow(protocol=protocal, port_expose='12345', prefetch=prefetch).add(
        uses=MyExecutor, parallel=parallel, polling=polling
    )

    with f:
        for t in thread_pool:
            t.start()

        for t in thread_pool:
            t.join()
    assert tasks.empty()
