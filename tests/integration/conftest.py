import os
import time

import pytest


@pytest.fixture()
def docker_image_name():
    return 'jina/replica-exec'


@pytest.fixture()
def docker_image_built(docker_image_name):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'replica-exec'), tag=docker_image_name
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()
