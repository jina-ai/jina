import os
import time
import pytest

import subprocess

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def docker_image():
    docker_file = os.path.join(cur_dir, 'Dockerfile')
    os.system(f"docker build -f {docker_file} -t clitest {cur_dir}")
    time.sleep(3)
    yield
    os.system(f"docker rmi -f $(docker images | grep 'clitest')")


def test_executor_cli_docker(docker_image):
    process = subprocess.Popen(
        ['jina', 'executor', '--uses', 'docker://clitest:latest']
    )
    time.sleep(5)
    poll = process.poll()
    process.terminate()
    assert poll is None


def test_zed_runtime_cli_docker(docker_image):
    process = subprocess.Popen(
        ['jina', 'executor', '--native', '--uses', 'docker://clitest:latest']
    )
    time.sleep(5)
    poll = process.poll()
    process.terminate()
    assert poll == 1  # failed
