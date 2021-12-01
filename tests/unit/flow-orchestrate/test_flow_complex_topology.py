import pytest

from jina import Flow, Document


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_flow_complex_toploogy(protocol):
    f = (
        Flow(protocol=protocol)
        .add(name='p2', needs='gateway')
        .add(name='p3', needs='gateway')
        .add(name='p2p3joiner', needs=['p2', 'p3'])
        .add(name='p5', needs='p2p3joiner')
        .add(name='p6', needs='p2p3joiner')
        .add(name='p7', needs=['p5', 'p6'])
    )

    with f:
        print(f' JOAN HERE PLOT')
        print(f.plot(build=False, copy_flow=False))
        res = f.index(Document(), return_results=True)

    assert len(res) > 0
