import os
import random
import string

import pytest
from fastapi.testclient import TestClient

from daemon.config import fastapi_config
from jina.executors.metas import get_default_metas

PREFIX = fastapi_config.PREFIX


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


@pytest.fixture(scope='session')
def fastapi_client():
    from daemon import _get_app
    app = _get_app()
    client = TestClient(app)
    return client


@pytest.fixture(scope='session')
def common_endpoints():
    return [
        ('openapi', '/openapi.json'),
        ('swagger_ui_html', '/docs'),
        ('swagger_ui_redirect', '/docs/oauth2-redirect'),
        ('redoc_html', '/redoc'),
        ('_status', f'{PREFIX}/alive'),
        ('LogStreamingEndpoint', f'{PREFIX}/logstream/{{log_id}}')
    ]


@pytest.fixture(scope='session')
def flow_endpoints():
    return [
        ('_create_from_pods', f'{PREFIX}/flow/pods'),
        ('_create_from_yaml', f'{PREFIX}/flow/yaml'),
        ('_fetch', f'{PREFIX}/flow/{{flow_id}}'),
        ('_ping', f'{PREFIX}/ping'),
        ('_delete', f'{PREFIX}/flow'),
    ]


@pytest.fixture(scope='session')
def pod_endpoints():
    return [
        ('_upload', f'{PREFIX}/upload'),
        ('_create', f'{PREFIX}/pod'),
        ('_delete', f'{PREFIX}/pod')
    ]


@pytest.fixture(scope='session')
def pea_endpoints():
    return [
        ('_upload', f'{PREFIX}/pea/upload'),
        ('_create', f'{PREFIX}/pea'),
        ('_delete', f'{PREFIX}/pea')
    ]
