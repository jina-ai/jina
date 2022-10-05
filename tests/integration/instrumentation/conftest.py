import os
import time

import pytest

from jina.logging.logger import JinaLogger


@pytest.fixture()
def otlp_collector():
    file_dir = os.path.dirname(__file__)
    os.system(
        f"docker-compose -f {os.path.join(file_dir, 'docker-compose.yml')} up -d --remove-orphans"
    )
    time.sleep(1)
    yield
    os.system(
        f"docker-compose -f {os.path.join(file_dir, 'docker-compose.yml')} down --remove-orphans"
    )
