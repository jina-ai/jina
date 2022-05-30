import pytest

from jina import Flow


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_health_check(protocol):
    f = Flow(protocol=protocol).add()
    with f:
        health_check = f.health_check()
    health_check_negative = f.health_check()

    assert health_check
    assert not health_check_negative
