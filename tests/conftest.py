import os
import pathlib
import random
import string
import time

import pytest
from fastapi.testclient import TestClient
from jina.excepts import NoAvailablePortError
from jina.executors.metas import get_default_metas


@pytest.fixture(scope='function')
def random_workspace_name():
    """Generate a random workspace name with digits and letters."""
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'JINA_TEST_WORKSPACE_{rand}'


@pytest.fixture(scope='function')
def test_metas(tmpdir, random_workspace_name):
    os.environ[random_workspace_name] = str(tmpdir)
    metas = get_default_metas()
    metas['workspace'] = os.environ[random_workspace_name]
    yield metas
    del os.environ[random_workspace_name]


@pytest.fixture(scope='function', autouse=False)
def fastapi_client():
    from daemon import __root_workspace__

    pathlib.Path(__root_workspace__).mkdir(parents=True, exist_ok=True)
    from daemon import _get_app

    app = _get_app()
    tc = TestClient(app)
    yield tc
    del tc


@pytest.fixture(scope='function', autouse=False)
def partial_flow_client(monkeypatch):
    yield from get_partial_client(mode='flow', monkeypatch=monkeypatch)


@pytest.fixture(scope='function', autouse=False)
def partial_pod_client(monkeypatch):
    yield from get_partial_client(mode='pod', monkeypatch=monkeypatch)


@pytest.fixture(scope='function', autouse=False)
def partial_pea_client(monkeypatch):
    yield from get_partial_client(mode='pea', monkeypatch=monkeypatch)


def get_partial_client(mode, monkeypatch):
    monkeypatch.setattr(os, "kill", lambda *args, **kwargs: None)
    from daemon import __root_workspace__

    pathlib.Path(__root_workspace__).mkdir(parents=True, exist_ok=True)
    from daemon import _get_app
    from daemon.models.enums import PartialDaemonModes
    from daemon import jinad_args

    jinad_args.mode = PartialDaemonModes.get_mode(mode)
    app = _get_app(mode=mode)
    tc = TestClient(app)
    yield tc
    del tc


@pytest.fixture()
def docker_compose(request):
    os.system(
        f"docker-compose -f {request.param} --project-directory . up  --build -d --remove-orphans"
    )
    time.sleep(5)
    yield
    os.system(
        f"docker-compose -f {request.param} --project-directory . down --remove-orphans"
    )


@pytest.fixture(scope='function', autouse=True)
def patched_random_port(mocker):
    used_ports = set()
    from jina.helper import random_port

    def _random_port():

        for i in range(10):
            _port = random_port()

            if _port is not None and _port not in used_ports:
                used_ports.add(_port)
                return _port
        raise NoAvailablePortError

    mocker.patch('jina.helper.random_port', new_callable=lambda: _random_port)
