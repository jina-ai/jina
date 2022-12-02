import functools
import time
from threading import Thread

import numpy as np
import pytest

from jina import Client, Document, Flow
from jina.helper import random_port


@pytest.mark.slow
@pytest.mark.parametrize('protocol', ['websocket', 'http'])
def test_gateway_concurrency(protocol, reraise):
    port = random_port()
    CONCURRENCY = 2

    def _validate(req, start, status_codes, durations, index):
        end = time.time()
        durations[index] = end - start
        status_codes[index] = req.status.code

    def _request(status_codes, durations, index):
        with reraise:
            start = time.time()
            on_done = functools.partial(
                _validate,
                start=start,
                status_codes=status_codes,
                durations=durations,
                index=index,
            )
            results = Client(port=port, protocol=protocol).index(
                inputs=(Document() for _ in range(256)), _size=16, return_responses=True
            )
            assert len(results) > 0
            for result in results:
                on_done(result)

    f = Flow(protocol=protocol, port=port).add(replicas=2)
    with f:
        threads = []
        status_codes = [None] * CONCURRENCY
        durations = [None] * CONCURRENCY
        for i in range(CONCURRENCY):
            t = Thread(target=_request, args=(status_codes, durations, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    success = status_codes.count(0)
    failed = len(status_codes) - success
    print(
        f'clients: {len(durations)}\n'
        f'min roundtrip time: {np.min(durations)}\n'
        f'max roundtrip time: {np.max(durations)}\n'
        f'mean roundtrip time: {np.mean(durations)}\n'
    )
    assert success >= 1
    # In some slow environments, a certain degree of failed
    # requests will occur. Here we limit the degree of failed
    # requests.
    rate = failed / success
    assert rate < 0.1


def test_grpc_custom_options():

    f = Flow(grpc_server_options={'grpc.max_send_message_length': -1})
    with f:
        pass
