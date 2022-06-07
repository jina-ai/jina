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
            self._process(docs)
            self.process_2(docs)

        @monitor(name='metrics_name', documentation='metrics description')
        def _process(self, docs):
            ...

        @monitor()
        def process_2(self, docs):
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
            f'jina_process_2_seconds_count{{runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )


def test_context_manager_interface(port_generator):
    class DummyExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):

            with self.monitor(
                name='process_seconds', documentation='process time in seconds '
            ):
                self._process(docs)

            with self.monitor(
                name='process_2_seconds', documentation='process 2 time in seconds '
            ):
                self.process_2(docs)

        def _process(self, docs):
            ...

        def process_2(self, docs):
            ...

    port = port_generator()
    with Flow(monitoring=True, port_monitoring=port_generator()).add(
        uses=DummyExecutor, monitoring=True, port_monitoring=port
    ) as f:
        f.post('/foo', inputs=DocumentArray.empty(4))

        resp = req.get(f'http://localhost:{port}/')
        assert (
            f'jina_process_seconds_count{{runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )
        assert (
            f'jina_process_2_seconds_count{{runtime_name="executor0/rep-0"}} 1.0'
            in str(resp.content)
        )
