import functools
import time
from threading import Thread

import numpy as np
import pytest
import requests

from jina.enums import CompressAlgo
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow
from tests import random_docs

concurrency = 10


class DummyEncoder(BaseEncoder):
    def encode(self, data, *args, **kwargs):
        pass


@pytest.mark.parametrize('compress_algo', list(CompressAlgo))
def test_compression(compress_algo):
    f = Flow(compress=str(compress_algo)).add(name='DummyEncoder', parallel=2)

    with f:
        f.index(random_docs(10))


@pytest.mark.skip('this test hangs up for unknown reason on github, works on local')
def test_rest_gateway_concurrency():
    def _request(status_codes, durations, index):
        resp = requests.post(
            f'http://0.0.0.0:{f.port_expose}/api/index',
            json={
                'data': [
                    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
                    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC']})
        durations[index] = resp.elapsed.total_seconds()
        status_codes[index] = resp.status_code

    f = Flow(rest_api=True).add(parallel=2)
    with f:
        concurrency = 50
        threads = []
        status_codes = [None] * concurrency
        durations = [None] * concurrency
        for i in range(concurrency):
            t = Thread(target=_request, args=(status_codes, durations, i))
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    success = status_codes.count(200)
    failed = len(status_codes) - success
    print(
        f'\nmin roundtrip time: {np.min(durations)}\n',
        f'max roundtrip time: {np.max(durations)}\n'
        f'mean roundtrip time: {np.mean(durations)}\n'
    )
    assert success >= 1
    # In some slow environments, a certain degree of failed
    # requests will occur. Here we limit the degree of failed
    # requests.
    rate = failed / success
    assert rate < 0.1


# TODO (Deepankar): change this to a Process rather than Thread & test
@pytest.mark.skip('raw grpc gateway is not stable enough under high concurrency')
def test_grpc_gateway_concurrency():
    def _input_fn():
        return iter([
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC'])

    def _validate(req, start, status_codes, durations, index):
        end = time.time()
        durations[index] = (end - start)
        status_codes[index] = req.status.code

    def _request(f, status_codes, durations, index):
        start = time.time()
        f.index(
            input_fn=_input_fn,
            on_done=functools.partial(
                _validate,
                start=start,
                status_codes=status_codes,
                durations=durations,
                index=index
            ))

    f = Flow().add(parallel=2)
    with f:
        threads = []
        status_codes = [None] * concurrency
        durations = [None] * concurrency
        for i in range(concurrency):
            t = Thread(
                target=_request, args=(
                    f, status_codes, durations, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
            print(f'terminate {t}')

    success = status_codes.count(0)
    failed = len(status_codes) - success
    print(
        f'\nmin roundtrip time: {np.min(durations)}\n',
        f'max roundtrip time: {np.max(durations)}\n'
        f'mean roundtrip time: {np.mean(durations)}\n'
    )
    assert success >= 1
    # In some slow environments, a certain degree of failed
    # requests will occur. Here we limit the degree of failed
    # requests.
    rate = failed / success
    assert rate < 0.1
