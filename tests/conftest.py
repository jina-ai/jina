import asyncio
import os
import pathlib
import random
import shutil
import string
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

from jina import helper


@pytest.fixture(scope='function')
def random_workspace_name():
    """Generate a random workspace name with digits and letters."""
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'JINA_TEST_WORKSPACE_{rand}'


@pytest.fixture(scope='function')
def test_metas(tmpdir, random_workspace_name):
    from jina.executors.metas import get_default_metas

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
    from daemon import __root_workspace__

    pathlib.Path(__root_workspace__).mkdir(parents=True, exist_ok=True)
    from daemon import _get_app
    from daemon.models.enums import PartialDaemonModes
    from daemon import jinad_args
    from daemon import stores
    from importlib import reload

    jinad_args.mode = PartialDaemonModes(mode)

    reload(stores)
    app = _get_app(mode=mode)
    tc = TestClient(app)
    yield tc
    del tc


@pytest.fixture()
def docker_compose(request):
    os.system(
        f"docker-compose -f {request.param} --project-directory . up  --build -d --remove-orphans"
    )
    time.sleep(10)
    yield
    os.system(
        f"docker-compose -f {request.param} --project-directory . down --remove-orphans"
    )


def _clean_up_workspace(image_id, network_id, workspace_id, workspace_store):
    from daemon.dockerize import Dockerizer

    import time

    time.sleep(1)
    Dockerizer.rm_image(image_id)
    Dockerizer.rm_network(network_id)
    workspace_store.delete(workspace_id, files=False)
    del workspace_store[workspace_id]
    workspace_store.dump(lambda *args, **kwargs: None)
    from daemon import stores
    from importlib import reload

    reload(stores)


def _create_workspace_directly(cur_dir):
    from daemon.models import DaemonID
    from daemon.helper import get_workspace_path
    from daemon.files import DaemonFile
    from daemon import daemon_logger
    from daemon.dockerize import Dockerizer
    from daemon.stores import workspace_store
    from daemon.models import WorkspaceItem
    from daemon.models.workspaces import WorkspaceMetadata
    from daemon.models.workspaces import WorkspaceArguments

    workspace_id = DaemonID('jworkspace')

    workdir = get_workspace_path(workspace_id)
    shutil.copytree(cur_dir, workdir)

    daemon_file = DaemonFile(
        workdir=get_workspace_path(workspace_id), logger=daemon_logger
    )

    image_id = Dockerizer.build(
        workspace_id=workspace_id, daemon_file=daemon_file, logger=daemon_logger
    )
    network_id = Dockerizer.network(workspace_id=workspace_id)
    from jina.enums import RemoteWorkspaceState

    workspace_store[workspace_id] = WorkspaceItem(
        state=RemoteWorkspaceState.ACTIVE,
        metadata=WorkspaceMetadata(
            image_id=image_id,
            image_name=workspace_id.tag,
            network=network_id,
            workdir=workdir,
        ),
        arguments=WorkspaceArguments(
            files=os.listdir(cur_dir), jinad={'a': 'b'}, requirements=''
        ),
    )
    return image_id, network_id, workspace_id, workspace_store


@pytest.fixture(scope='function')
def port_generator():
    generated_ports = set()

    def random_port():
        port = helper.random_port()
        while port in generated_ports:
            port = helper.random_port()
        generated_ports.add(port)
        return port

    return random_port


@pytest.fixture(scope='function')
def test_envs(tmpdir):
    os.environ['JINA_HUB_ROOT'] = str(tmpdir)
    os.environ['JINA_HUB_CACHE_DIR'] = str(tmpdir)
    yield None
    del os.environ['JINA_HUB_ROOT']
    del os.environ['JINA_HUB_CACHE_DIR']


@pytest.fixture(autouse=True)
def test_log_level(monkeypatch):
    monkeypatch.setenv('JINA_LOG_LEVEL', 'DEBUG')


@pytest.fixture(autouse=True)
def test_timeout_ctrl_time(monkeypatch):
    monkeypatch.setenv('JINA_DEFAULT_TIMEOUT_CTRL', '500')


@pytest.fixture(autouse=True)
def tmpfile(tmpdir):
    tmpfile = f'jina_test_{next(tempfile._get_candidate_names())}.db'
    return tmpdir / tmpfile


@pytest.fixture(scope='session')
def event_loop(request):
    """
    Valid only for `pytest.mark.asyncio` tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
