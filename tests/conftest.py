import os
import random
import string
import time

import pytest
from fastapi.testclient import TestClient

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
    from daemon import _get_app
    app = _get_app()
    tc = TestClient(app)
    yield tc
    del tc


@pytest.fixture(scope='session')
def common_endpoints():
    return [
        ('openapi', '/openapi.json'),
        ('swagger_ui_html', '/docs'),
        ('swagger_ui_redirect', '/docs/oauth2-redirect'),
        ('redoc_html', '/redoc'),
        ('_status', f'/alive'),
        ('LogStreamingEndpoint', f'/logstream/{{log_id}}')
    ]


@pytest.fixture(scope='session')
def flow_endpoints():
    return [
        ('_fetch_flow_params', '/flow/parameters'),
        ('_create_from_pods', '/flow/pods'),
        ('_create_from_yaml', '/flow/yaml'),
        ('_fetch', f'/flow/{{flow_id}}'),
        ('_ping', '/ping'),
        ('_delete', '/flow'),
    ]


@pytest.fixture(scope='session')
def pod_endpoints():
    return [
        ('_fetch_pod_params', '/pod/parameters'),
        ('_upload', '/upload'),
        ('_create', '/pod'),
        ('_delete', '/pod')
    ]


@pytest.fixture(scope='session')
def pea_endpoints():
    return [
        ('_fetch_pea_params', '/pea/parameters'),
        ('_upload', '/pea/upload'),
        ('_create', '/pea'),
        ('_delete', '/pea')
    ]


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
