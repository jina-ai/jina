import requests as req
from docarray import DocumentArray
from prometheus_client import Summary

from jina import Executor, Flow, monitor, requests


def test_prometheus_interface(port_generator):
    class DummyExecutor(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.summary = Summary(
                'a', 'A', registry=self.runtime_args.metrics_registry
            )

        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            with self.summary.time():
                ...

    port = port_generator()
    with Flow(monitoring=True, port_monitoring=port_generator()).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port
    ) as f:
        f.post('/foo', inputs=DocumentArray.empty(4))

        resp = req.get(f'http://localhost:{port}/')
        assert f'a_count 1.0' in str(  # check that we count 4 documents on foo
            resp.content
        )


def test_decorator_interface(port_generator):
    class DummyExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            self._proces(docs)
            self.proces_2(docs)

        @monitor(name='metrics_name', documentation='metrics description')
        def _proces(self, docs):
            ...

        @monitor()
        def proces_2(self, docs):
            ...

    port = port_generator()
    with Flow(monitoring=True, port_monitoring=port_generator()).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port
    ) as f:
        f.post('/foo', inputs=DocumentArray.empty(4))

        resp = req.get(f'http://localhost:{port}/')
        assert f'jina_metrics_name_count{{runtime_name="executor0/rep-0"}} 1.0' in str(
            resp.content
        )
        assert (
            f'jina_proces_2_seconds_count{{runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )
