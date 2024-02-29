import pytest

from jina import Executor, Flow, requests


@pytest.fixture()
def get_executor():
    class DummyExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs): ...

    return DummyExecutor


def test_disable_monitoring_on_pods(port_generator, get_executor):
    port0 = port_generator()
    port1 = port_generator()

    f = Flow(monitoring=True, port_monitoring=port0).add(
        uses=get_executor(),
        port_monitoring=port1,
        monitoring=False,
    )

    f = f.build()

    assert f._deployment_nodes['gateway'].pod_args['pods'][0][0].monitoring
    assert not f._deployment_nodes['executor0'].pod_args['pods'][0][0].monitoring


def test_disable_monitoring_on_gatway_only(port_generator, get_executor):
    port0 = port_generator()
    port1 = port_generator()

    f = Flow(monitoring=False, port_monitoring=port0).add(
        uses=get_executor(),
        port_monitoring=port1,
        monitoring=True,
    )

    f = f.build()

    assert not f._deployment_nodes['gateway'].pod_args['pods'][0][0].monitoring
    assert f._deployment_nodes['executor0'].pod_args['pods'][0][0].monitoring
