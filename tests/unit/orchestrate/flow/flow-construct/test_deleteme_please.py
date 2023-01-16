import time

from jina import Executor, Flow, requests


class E(Executor):
    @requests
    def do_something(self, *args, **kwargs):
        time.sleep(2)
        print('do something')


def test_multiple_flow_executions():
    for i in range(10):
        print('i', i)
        with (
            Flow().add(
                uses=E,
            )
        ) as f:
            pass
