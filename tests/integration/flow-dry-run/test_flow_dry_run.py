import pytest

from jina import Flow


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_dry_run(protocol):
    f = Flow(protocol=protocol).add()
    with f:
        dry_run = f.dry_run()
    dry_run_negative = f.dry_run()

    assert dry_run
    assert not dry_run_negative
