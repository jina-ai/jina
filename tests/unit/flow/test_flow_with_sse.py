import pytest

from jina.flow import Flow


@pytest.mark.timeout(60)
@pytest.mark.repeat(10)
def test_flow_with_sse():
    f = Flow(logserver=True). \
        add(uses='BaseExecutor', parallel=1).add(uses='BaseExecutor', parallel=2).build()
    with f:
        assert hasattr(f, '_sse_logger')
        pass
