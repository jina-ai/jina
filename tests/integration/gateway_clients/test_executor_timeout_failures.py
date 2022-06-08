import multiprocessing
import time

import pytest

from jina import Client, Document, Executor, Flow, requests


class SlowExecutor(Executor):
    @requests
    def foo(self, *args, **kwargs):
        time.sleep(0.2)


def _test_error(flow, error_port=None):
    with flow:
        with pytest.raises(ConnectionError) as err_info:
            flow.index(inputs=[])
    if error_port:
        assert str(error_port) in err_info.value.args[0]


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_headless_exec_timeout(port_generator, protocol):
    exec_port = port_generator()
    f = Flow(timeout_send=1, protocol=protocol).add(uses=SlowExecutor, port=exec_port)

    # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
    p = multiprocessing.Process(target=_test_error, args=(f, exec_port))
    p.start()
    p.join()
    assert (
        p.exitcode == 0
    )  # if exitcode != 0 then test in other process did not pass and this should fail


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_headfull_exec_timeout(port_generator, protocol):
    f = Flow(timeout_send=1, protocol=protocol).add(uses=SlowExecutor, shards=2)

    # we have to do this in a new process because otherwise grpc will be sad and everything will crash :(
    p = multiprocessing.Process(target=_test_error, args=(f,))
    p.start()
    p.join()
    assert (
        p.exitcode == 0
    )  # if exitcode != 0 then test in other process did not pass and this should fail
