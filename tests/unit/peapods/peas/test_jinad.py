import random
import asyncio
import pytest
from jina.parsers import set_pea_parser
from jina.peapods.peas import jinad
from jina.peapods.peas.jinad import JinaDProcessTarget, JinaDPea


async def mock_sleep(*args):
    await asyncio.sleep(random.random())


def mock_is_ready(*args):
    return True


@pytest.mark.parametrize('runtime_backend', ['PROCESS', 'THREAD'])
def test_events(monkeypatch, runtime_backend):
    monkeypatch.setattr(JinaDProcessTarget, '_create_remote_pea', mock_sleep)
    monkeypatch.setattr(JinaDProcessTarget, '_terminate_remote_pea', mock_sleep)
    monkeypatch.setattr(JinaDProcessTarget, '_stream_logs', mock_sleep)
    monkeypatch.setattr(jinad, 'is_ready', mock_is_ready)
    args = set_pea_parser().parse_args(['--runtime-backend', runtime_backend])

    pea = JinaDPea(args)
    assert not pea.is_started.is_set()
    assert not pea.is_ready.is_set()
    assert not pea.is_shutdown.is_set()
    assert not pea.cancel_event.is_set()

    with pea:
        assert pea.is_started.is_set()
        assert pea.is_ready.is_set()
    assert pea.is_shutdown.is_set()
