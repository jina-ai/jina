import pytest

from jina.types.request.common import (
    DryRunRequest,
    IndexDryRunRequest,
    TrainDryRunRequest,
    ControlDryRunRequest,
    SearchDryRunRequest
)

@pytest.mark.parametrize(
    'ReqCls', [DryRunRequest, IndexDryRunRequest, TrainDryRunRequest, ControlDryRunRequest, SearchDryRunRequest]
)
def test_init(ReqCls):
    assert ReqCls()

