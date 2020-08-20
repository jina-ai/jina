import os
import time
from sys import platform

import pytest

from jina.flow import Flow
from jina.main.checker import NetworkChecker
from jina.main.parser import set_pea_parser, set_ping_parser
from jina.peapods.container import ContainerPea
from jina.peapods.pea import BasePea
from tests import JinaTestCase, random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))

built = False
img_name = 'jina/mwu-encoder'

defaulthost = '0.0.0.0'
localhost = defaulthost if (platform == "linux" or platform == "linux2") else 'host.docker.internal'


def build_image():
    if not built:
        import docker
        client = docker.from_env()
        client.images.build(path=os.path.join(cur_dir, 'mwu-encoder/'), tag=img_name)
        client.close()


# @unittest.skipUnless(os.getenv('JINA_TEST_CONTAINER', False), 'skip the container test if not set')
class MyTestCase(JinaTestCase):

    def tearDown(self) -> None:
        super().tearDown()
        time.sleep(2)

    def setUp(self) -> None:
        super().setUp()
        build_image()

    def test_simple_container(self):
        args = set_pea_parser().parse_args(['--uses', img_name])
        print(args)

        with ContainerPea(args):
            pass

        time.sleep(2)
        ContainerPea(args).start().close()

    def test_simple_container_with_ext_yaml(self):
        args = set_pea_parser().parse_args(['--uses', img_name,
                                            '--uses-internal', os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_ext.yml')])
        print(args)

        with ContainerPea(args):
            time.sleep(2)

    def test_flow_with_one_container_pod(self):
        f = (Flow()
             .add(name='dummyEncoder', uses=img_name))

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_with_one_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder', uses=img_name,
                  uses_internal=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_ext.yml')))

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_with_replica_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder',
                  uses=img_name,
                  uses_internal=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_ext.yml'),
                  parallel=3))

        with f:
            f.index(input_fn=random_docs(10))
            f.index(input_fn=random_docs(10))
            f.index(input_fn=random_docs(10))

    def test_flow_topo1(self):
        f = (Flow()
             .add(name='d1', uses='jinaai/jina:test-pip', uses_internal='_logforward', entrypoint='jina pod')
             .add(name='d2', uses='jinaai/jina:test-pip', uses_internal='_logforward', entrypoint='jina pod')
             .add(name='d3', uses='jinaai/jina:test-pip', uses_internal='_logforward',
                  needs='d1', entrypoint='jina pod')
             .join(['d3', 'd2']))

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_topo_mixed(self):
        f = (Flow()
             .add(name='d1', uses='jinaai/jina:test-pip', uses_internal='_logforward', entrypoint='jina pod')
             .add(name='d2', uses='_logforward')
             .add(name='d3', uses='jinaai/jina:test-pip', uses_internal='_logforward',
                  needs='d1', entrypoint='jina pod')
             .join(['d3', 'd2'])
             )

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_topo_parallel(self):
        f = (Flow()
             .add(name='d1', uses='jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass', parallel=3)
             .add(name='d2', uses='_pass', parallel=3)
             .add(name='d3', uses='jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass',
                  needs='d1')
             .join(['d3', 'd2'])
             )

        with f:
            f.dry_run()
            f.index(input_fn=random_docs(1000))

    @pytest.mark.skip('extract_docs throw an error')
    def test_container_volume(self):
        time.sleep(5)
        f = (Flow()
             .add(name='dummyEncoder', uses=img_name, volumes='./abc',
                  uses_internal=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_upd.yml')))

        with f:
            f.index(input_fn=random_docs(10))

        out_file = 'abc/ext-mwu-encoder.bin'
        self.assertTrue(os.path.exists(os.path.join(cur_dir, out_file)))
        self.add_tmpfile(out_file, './abc')

    def test_container_ping(self):
        a4 = set_pea_parser().parse_args(['--uses', img_name])
        a5 = set_ping_parser().parse_args(['0.0.0.0', str(a4.port_ctrl), '--print-response'])

        # test with container
        with self.assertRaises(SystemExit) as cm:
            with BasePea(a4):
                NetworkChecker(a5)

        assert cm.exception.code == 0

    def test_tail_host_docker2local_parallel(self):
        f = (Flow()
             .add(name='d1', uses='jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass', parallel=3)
             .add(name='d2', uses='_pass'))
        with f:
            assert getattr(f._pod_nodes['d1'].peas_args['tail'], 'host_out') == defaulthost
            f.dry_run()

    def test_tail_host_docker2local(self):
        f = (Flow()
             .add(name='d1', uses='jinaai/jina:test-pip', entrypoint='jina pod', uses_internal='_pass')
             .add(name='d2', uses='_pass'))
        with f:
            assert getattr(f._pod_nodes['d1'].tail_args, 'host_out') == localhost
            f.dry_run()
