import os
import time
import pytest

import subprocess

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def docker_image():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir), tag='clitest')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def test_executor_cli_docker(docker_image):
    process = subprocess.Popen(
        ['jina', 'executor', '--uses', 'docker://clitest:latest']
    )
    time.sleep(5)
    poll = process.poll()
    process.terminate()
    assert poll is None
