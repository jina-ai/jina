import os

import pytest

from jina import Flow
from jina.executors import BaseExecutor


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='skip the test on github as it will hang the whole CI, locally is fine',
)
def test_flow_simple_reload(mocker):
    mock = mocker.Mock()

    class DummyExecutor(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            mock()

    f = Flow().add(name='mypod', uses=DummyExecutor, runtime_backend='thread')

    with f:
        pass

    assert mock.call_count == 1

    mock.reset_mock()
    with f:
        f.reload(targets='mypod')

    assert mock.call_count == 2


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='skip the test on github as it will hang the whole CI, locally is fine',
)
def test_flow_topology_multi_reload(mocker):
    mock1 = mocker.Mock()
    mock2 = mocker.Mock()

    class DummyExecutor1(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            mock1()

    class DummyExecutor2(BaseExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            mock2()

    f = (
        Flow()
        .add(name='mypod', uses=DummyExecutor1, runtime_backend='thread')
        .add(runtime_backend='thread')
        .add(name='yourpod', uses=DummyExecutor2, runtime_backend='thread')
        .needs_all(runtime_backend='thread')
    )

    with f:
        pass

    assert mock1.call_count == 1
    assert mock2.call_count == 1

    mock1.reset_mock()
    mock2.reset_mock()

    with f:
        f.reload(targets='mypod')
        assert mock1.call_count == 2
        assert mock2.call_count == 1
        f.reload(targets='yourpod')
        assert mock1.call_count == 2
        assert mock2.call_count == 2
        f.reload(targets='.*pod')
        assert mock1.call_count == 3
        assert mock2.call_count == 3
