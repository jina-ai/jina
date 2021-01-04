import os
import time
from sys import platform

import pytest

from jina.checker import NetworkChecker
from jina.flow import Flow
from jina.helper import random_name
from jina.parsers import set_pea_parser
from jina.parsers.ping import set_ping_parser
from jina.peapods import Pea
from jina.peapods.runtimes.container import ContainerRuntime
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))

img_name = 'jina/mwu-encoder'

defaulthost = '0.0.0.0'
localhost = defaulthost if (platform == "linux" or platform == "linux2") else 'host.docker.internal'


@pytest.fixture(scope='module')
def docker_image_built():
    import docker
    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, '../../../mwu-encoder/'), tag=img_name)
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def test_simple_container(docker_image_built):
    args = set_pea_parser().parse_args(['--uses', f'docker://{img_name}'])

    with Pea(args):
        pass

    time.sleep(2)
    Pea(args).start().close()


@pytest.mark.skip(reason='flaky, will be refactored as part of #1539')
def test_simple_container_with_ext_yaml(docker_image_built):
    args = set_pea_parser().parse_args(['--uses', f'docker://{img_name}',
                                        '--uses-internal',
                                        os.path.join(cur_dir, '../../../mwu-encoder/mwu_encoder_ext.yml')])

    with Pea(args):
        time.sleep(2)


def test_flow_with_one_container_pod(docker_image_built):
    f = (Flow()
         .add(name='dummyEncoder1', uses=f'docker://{img_name}'))

    with f:
        f.index(input_fn=random_docs(10))


def test_flow_with_one_container_ext_yaml(docker_image_built):
    f = (Flow()
         .add(name='dummyEncoder2', uses=f'docker://{img_name}',
              uses_internal=os.path.join(cur_dir, '../../../mwu-encoder/mwu_encoder_ext.yml')))

    with f:
        f.index(input_fn=random_docs(10))


def test_flow_with_replica_container_ext_yaml(docker_image_built):
    f = (Flow()
         .add(name='dummyEncoder3',
              uses=f'docker://{img_name}',
              uses_internal=os.path.join(cur_dir, '../../../mwu-encoder/mwu_encoder_ext.yml'),
              parallel=3))

    with f:
        f.index(input_fn=random_docs(10))
        f.index(input_fn=random_docs(10))
        f.index(input_fn=random_docs(10))


def test_flow_topo1(docker_image_built):
    f = (Flow()
         .add(name='d0', uses='docker://jinaai/jina:test-pip', uses_internal='_logforward', entrypoint='jina pod')
         .add(name='d1', uses='docker://jinaai/jina:test-pip', uses_internal='_logforward', entrypoint='jina pod')
         .add(name='d2', uses='docker://jinaai/jina:test-pip', uses_internal='_logforward',
              needs='d0', entrypoint='jina pod')
         .join(['d2', 'd1']))

    with f:
        f.index(input_fn=random_docs(10))


def test_flow_topo_mixed(docker_image_built):
    f = (Flow()
         .add(name='d4', uses='docker://jinaai/jina:test-pip', uses_internal='_logforward', entrypoint='jina pod')
         .add(name='d5', uses='_logforward')
         .add(name='d6', uses='docker://jinaai/jina:test-pip', uses_internal='_logforward',
              needs='d4', entrypoint='jina pod')
         .join(['d6', 'd5']))

    with f:
        f.index(input_fn=random_docs(10))


def test_flow_topo_parallel(docker_image_built):
    f = (Flow()
         .add(name='d7', uses='docker://jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass', parallel=3)
         .add(name='d8', parallel=3)
         .add(name='d9', uses='docker://jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass',
              needs='d7')
         .join(['d9', 'd8']))

    with f:
        f.index(input_fn=random_docs(1000))


def test_container_volume(docker_image_built, tmpdir):
    abc_path = os.path.join(tmpdir, 'abc')
    f = (Flow()
         .add(name=random_name(), uses=f'docker://{img_name}', volumes=abc_path,
              uses_internal=os.path.join(cur_dir, '../../../mwu-encoder/mwu_encoder_upd.yml')))

    with f:
        f.index(random_docs(10))

    assert os.path.exists(os.path.join(abc_path, 'ext-mwu-encoder.bin'))


def test_container_ping(docker_image_built):
    a4 = set_pea_parser().parse_args(['--uses', f'docker://{img_name}'])
    a5 = set_ping_parser().parse_args(['0.0.0.0', str(a4.port_ctrl), '--print-response'])

    # test with container
    with pytest.raises(SystemExit) as cm:
        with Pea(a4):
            NetworkChecker(a5)

    assert cm.value.code == 0


def test_tail_host_docker2local_parallel(docker_image_built):
    f = (Flow()
         .add(name='d10', uses='docker://jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass', parallel=3)
         .add(name='d11'))
    with f:
        assert getattr(f._pod_nodes['d10'].peas_args['tail'], 'host_out') == defaulthost


def test_tail_host_docker2local(docker_image_built):
    f = (Flow()
         .add(name='d12', uses='docker://jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass')
         .add(name='d13'))
    with f:
        assert getattr(f._pod_nodes['d12'].tail_args, 'host_out') == localhost
