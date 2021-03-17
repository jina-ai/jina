import functools
import time
from threading import Thread

import numpy as np
import pytest

from jina import Document
from jina.drivers.control import BaseControlDriver
from jina.enums import CompressAlgo
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from tests import random_docs


class DummyEncoder(BaseEncoder):
    def encode(self, data, *args, **kwargs):
        pass


@pytest.mark.parametrize('compress_algo', list(CompressAlgo))
def test_compression(compress_algo, mocker):
    class CompressCheckDriver(BaseControlDriver):
        def __call__(self, *args, **kwargs):
            assert self.req._envelope.compression.algorithm == str(compress_algo)

    response_mock = mocker.Mock()

    f = (
        Flow(compress=str(compress_algo))
        .add(uses='- !CompressCheckDriver {}')
        .add(name='DummyEncoder', parallel=2)
        .add(uses='- !CompressCheckDriver {}')
    )

    with f:
        f.index(random_docs(10), on_done=response_mock)

    response_mock.assert_called()


@pytest.mark.parametrize('rest_api', [True, False])
def test_grpc_gateway_concurrency(rest_api):
    def _validate(req, start, status_codes, durations, index):
        end = time.time()
        durations[index] = end - start
        status_codes[index] = req.status.code

    def _request(f, status_codes, durations, index):
        start = time.time()
        f.index(
            inputs=(Document() for _ in range(256)),
            on_done=functools.partial(
                _validate,
                start=start,
                status_codes=status_codes,
                durations=durations,
                index=index,
            ),
            batch_size=16,
        )

    f = Flow(restful=rest_api).add(parallel=2)
    concurrency = 100
    with f:
        threads = []
        status_codes = [None] * concurrency
        durations = [None] * concurrency
        for i in range(concurrency):
            t = Thread(target=_request, args=(f, status_codes, durations, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
            print(f'terminate {t}')

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
