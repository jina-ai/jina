import random
import asyncio
import pytest
from jina.parsers import set_pod_parser
from jina.orchestrate.pods import jinad
from jina.orchestrate.pods.jinad import JinaDProcessTarget, JinaDPod


async def mock_sleep(*args):
    await asyncio.sleep(random.random())


def mock_is_ready(*args):
    return True


# TODO enable this test once jinad is implemented
@pytest.mark.skip(
    "Does not work for some reason, should be reenabled when jinad is properly implemented"
)
def test_events(monkeypatch):
    monkeypatch.setattr(JinaDProcessTarget, '_create_remote_pod', mock_sleep)
    monkeypatch.setattr(JinaDProcessTarget, '_terminate_remote_pod', mock_sleep)
    monkeypatch.setattr(JinaDProcessTarget, '_stream_logs', mock_sleep)
    monkeypatch.setattr(jinad, 'is_ready', mock_is_ready)
    args = set_pod_parser().parse_args([])

    pod = JinaDPod(args)
    assert not pod.is_started.is_set()
    assert not pod.is_ready.is_set()
    assert not pod.is_shutdown.is_set()
    assert not pod.cancel_event.is_set()

    with pod:
        assert pod.is_started.is_set()
        assert pod.is_ready.is_set()
    assert pod.is_shutdown.is_set()
