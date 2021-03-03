import os
import numpy as np
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
    from daemon import _get_app
    app = _get_app()
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
    def _random_port():

        def _sample_random_port():
            import threading
            import multiprocessing
            from contextlib import closing
            import socket

            def _get_port(port=0):
                with multiprocessing.Lock():
                    with threading.Lock():
                        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                            try:
                                s.bind(('', port))
                                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                return s.getsockname()[1]
                            except OSError:
                                pass

            _port = None
            if 'JINA_RANDOM_PORTS' in os.environ:
                min_port = int(os.environ.get('JINA_RANDOM_PORT_MIN', '49153'))
                max_port = int(os.environ.get('JINA_RANDOM_PORT_MAX', '65535'))
                for _port in np.random.permutation(range(min_port, max_port + 1)):
                    if _get_port(_port) is not None:
                        break
                else:
                    raise OSError(f'Couldn\'t find an available port in [{min_port}, {max_port}].')
            else:
                _port = _get_port()

            return int(_port)

        for i in range(10):
            _port = _sample_random_port()

            if _port is not None and _port not in used_ports:
                used_ports.add(_port)
                return _port
        raise NoAvailablePortError

    mocker.patch('jina.helper.random_port', new_callable=lambda: _random_port)

