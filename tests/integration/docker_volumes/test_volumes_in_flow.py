import os
import time

import pytest
from docarray import Document

from jina import Flow
from jina.constants import __cache_path__

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def filewriter_exec_docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, 'filewriter-exec/'), tag='filewriter-exec'
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize(
    'source,destination,workspace',
    [('test/dir', '/custom/app', '/custom/app')],
)
def test_volumes_in_flow(
    tmpdir, source, destination, workspace, filewriter_exec_docker_image_built
):
    if source:  # test manually set volume and workspace
        source = os.path.join(tmpdir, source)
        volumes = [str(source) + ':' + destination]
    else:  # test auto volume and workspace
        source = __cache_path__

    f = Flow().add(
        uses='docker://filewriter-exec', volumes=volumes, workspace=workspace
    )
    with f:
        f.post(inputs=[Document()], on='/foo')

    assert os.path.exists(source)

    found_output_file = False  # workspace has random element, so we search for it
    for cur_path, dirs, files in os.walk(source):
        if 'out.txt' in files:
            with open(os.path.join(cur_path, 'out.txt'), 'r', encoding='utf-8') as f:
                if f.read() == 'Filewriter was here':
                    found_output_file = True
    assert found_output_file
