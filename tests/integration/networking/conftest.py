import pytest

from jina.logging.logger import JinaLogger
from jina.serve.networking import _NetworkingMetrics


@pytest.fixture()
def logger():
    return JinaLogger('test networking')


@pytest.fixture()
def metrics():
    sending_requests_time_metrics = None
    received_response_bytes = None
    send_requests_bytes_metrics = None

    return _NetworkingMetrics(
        sending_requests_time_metrics,
        received_response_bytes,
        send_requests_bytes_metrics,
    )
