import pytest

from jina import Flow, Executor, Client, requests, DocumentArray, Document
import threading
import random
import time
from functools import partial

from jina.types.request.data import Response


class MyExecutor(Executor):
    @requests(on='/ping')
    def ping(self, **kwargs):
        time.sleep(0.1 * random.random())


@pytest.mark.parametrize('protocol', ['grpc', 'http'])
@pytest.mark.parametrize('shards', [10])
@pytest.mark.parametrize('polling', ['ANY', 'ALL'])
@pytest.mark.parametrize('prefetch', [1, 10])
@pytest.mark.parametrize('concurrent', [15])
def test_concurrent_clients(concurrent, protocol, shards, polling, prefetch, reraise):
    def peer_client(clients_served_set, port, protocal, peer_hash):
        with reraise:
            c = Client(protocol=protocal, port=port)
            for _ in range(5):
                resp = c.post('/ping', Document(text=peer_hash), return_results=True)
                assert len(resp) == 1
                assert len(resp[0].docs) == 1
                for d in resp[0].docs:
                    assert d.text == peer_hash
                    clients_served_set.add(int(d.text))

    f = Flow(protocol=protocol, prefetch=prefetch).add(
        uses=MyExecutor, shards=shards, polling=polling
    )

    set_of_clients_served = set()

    with f:
        port_expose = f.port_expose
        thread_pool = []
        for peer_id in range(concurrent):
            t = threading.Thread(
                target=partial(
                    peer_client,
                    set_of_clients_served,
                    port_expose,
                    protocol,
                    str(peer_id),
                ),
                daemon=True,
            )
            t.start()
            thread_pool.append(t)

        for t in thread_pool:
            t.join()

    assert set_of_clients_served == set(list(range(concurrent)))
