import pytest

from jina import Flow
from jina.excepts import FlowTopologyError


def test_flow_error_frozen_pod():
    flow = (
        Flow()
        .add(port_out=5000, freeze_network_settings=True)
        .add(port_in=3000, freeze_network_settings=True)
    )

    with pytest.raises(FlowTopologyError):
        with flow:
            pass
