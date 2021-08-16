# Contains reusable fixtures for the kubernetes testing module
import os
import pytest
import docker

from jina.logging.logger import JinaLogger

client = docker.from_env()
cur_dir = os.path.dirname(__file__)


@pytest.fixture()
def logger():
    logger = JinaLogger('kubernetes-testing')
    return logger


@pytest.fixture()
def executor_image(logger: JinaLogger):
    image, build_logs = client.images.build(path=os.path.join(cur_dir, 'test-executor'), tag='test-executor:v.0.1', rm=True)
    for chunk in build_logs:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
    return image
