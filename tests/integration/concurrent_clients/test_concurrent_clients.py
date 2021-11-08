import pytest

from jina import Flow, Executor, Client, requests, DocumentArray, Document
from jina.types.request import Response
import threading
import random
import time
from functools import partial


class MyExecutor(Executor):
    @requests(on='/ping')
    def ping(self, docs: DocumentArray, **kwargs):
        time.sleep(0.1 * random.random())


@pytest.mark.parametrize('protocal', ['http', 'grpc'])
@pytest.mark.parametrize('shards', [10])
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
@pytest.mark.parametrize('prefetch', [1, 10])
@pytest.mark.parametrize('concurrent', [15])
def test_concurrent_clients(concurrent, protocal, shards, polling, prefetch, reraise):
    def pong(peer_hash, resp: Response):
        with reraise:
            for d in resp.docs:
                assert d.text == peer_hash

    def peer_client(port, protocal, peer_hash):
        c = Client(protocol=protocal, port=port)
        for _ in range(5):
            c.post(
                '/ping', Document(text=peer_hash), on_done=lambda r: pong(peer_hash, r)
            )

    f = Flow(protocol=protocal, prefetch=prefetch).add(
        uses=MyExecutor, shards=shards, polling=polling
    )

    with f:
        port_expose = f.port_expose

        thread_pool = []
        for peer_id in range(concurrent):
            t = threading.Thread(
                target=partial(peer_client, port_expose, protocal, str(peer_id)),
                daemon=True,
            )
            t.start()
            thread_pool.append(t)

        for t in thread_pool:
            t.join()
