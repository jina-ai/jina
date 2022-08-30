import time

import pytest
from docarray import DocumentArray

from jina import Executor, Flow, requests


@pytest.fixture()
def slow_executor() -> Executor:
    class MySlowExec(Executor):
        @requests
        def slow(self, docs, **kwargs):
            time.sleep(30)
            for doc_ in docs:
                doc_.text = 'process'

    return MySlowExec


@pytest.mark.slow
def test_long_flow_keep_alive(slow_executor):
    # it tests that the connection to a flow that take a lot of time to process will not be killed by the keepalive feature

    with Flow().add(uses=slow_executor) as f:
        docs = f.search(inputs=DocumentArray.empty(10))

    for doc_ in docs:
        assert doc_.text == 'process'
