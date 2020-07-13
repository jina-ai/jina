import os
import time
from sys import platform
import pytest

from jina.flow import Flow
from jina.main.checker import NetworkChecker
from jina.main.parser import set_pea_parser, set_ping_parser
from jina.peapods.container import ContainerPea
from jina.peapods.pea import BasePea
from jina.proto import jina_pb2
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d


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
        args = set_pea_parser().parse_args(['--image', img_name])
        print(args)

        with ContainerPea(args):
            pass

        time.sleep(2)
        ContainerPea(args).start().close()

    def test_simple_container_with_ext_yaml(self):
        args = set_pea_parser().parse_args(['--image', img_name,
                                            '--yaml-path', os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_ext.yml')])
        print(args)

        with ContainerPea(args):
            time.sleep(2)

    def test_flow_with_one_container_pod(self):
        f = (Flow()
             .add(name='dummyEncoder', image=img_name))

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_with_one_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder', image=img_name,
                  yaml_path=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_ext.yml')))

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_with_replica_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder',
                  image=img_name,
                  yaml_path=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_ext.yml'),
                  replicas=3))

        with f:
            f.index(input_fn=random_docs(10))
            f.index(input_fn=random_docs(10))
            f.index(input_fn=random_docs(10))

    def test_flow_topo1(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:test-pip', yaml_path='_logforward', entrypoint='jina pod')
             .add(name='d2', image='jinaai/jina:test-pip', yaml_path='_logforward', entrypoint='jina pod')
             .add(name='d3', image='jinaai/jina:test-pip', yaml_path='_logforward',
                  needs='d1', entrypoint='jina pod')
             .join(['d3', 'd2']))

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_topo_mixed(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:test-pip', yaml_path='_logforward', entrypoint='jina pod')
             .add(name='d2', yaml_path='_logforward')
             .add(name='d3', image='jinaai/jina:test-pip', yaml_path='_logforward',
                  needs='d1', entrypoint='jina pod')
             .join(['d3', 'd2'])
             )

        with f:
            f.index(input_fn=random_docs(10))

    def test_flow_topo_replicas(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:test-pip', entrypoint='jina pod', yaml_path='_forward', replicas=3)
             .add(name='d2', yaml_path='_forward', replicas=3)
             .add(name='d3', image='jinaai/jina:test-pip', entrypoint='jina pod', yaml_path='_forward',
                  needs='d1')
             .join(['d3', 'd2'])
             )

        with f:
            f.dry_run()
            f.index(input_fn=random_docs(1000))

    @pytest.mark.skip('this leads to zmq address conflicts on github')
    def test_container_volume(self):
        time.sleep(5)
        f = (Flow()
             .add(name='dummyEncoder', image=img_name, volumes='./abc',
                  yaml_path=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_upd.yml')))

        with f:
            f.index(input_fn=random_docs(10))

        out_file = 'abc/ext-mwu-encoder.bin'
        self.assertTrue(os.path.exists(out_file))
        self.add_tmpfile(out_file, './abc')

    def test_container_ping(self):
        a4 = set_pea_parser().parse_args(['--image', img_name])
        a5 = set_ping_parser().parse_args(['0.0.0.0', str(a4.port_ctrl), '--print-response'])

        # test with container
        with self.assertRaises(SystemExit) as cm:
            with BasePea(a4):
                NetworkChecker(a5)

        self.assertEqual(cm.exception.code, 0)

    def test_tail_host_docker2local_replicas(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:test-pip', entrypoint='jina pod', yaml_path='_forward', replicas=3)
             .add(name='d2', yaml_path='_forward'))
        with f:
            self.assertEqual(getattr(f._pod_nodes['d1'].peas_args['tail'], 'host_out'), defaulthost)
            f.dry_run()

    def test_tail_host_docker2local(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:test-pip', entrypoint='jina pod', yaml_path='_forward')
             .add(name='d2', yaml_path='_forward'))
        with f:
            self.assertEqual(getattr(f._pod_nodes['d1'].tail_args, 'host_out'), localhost)
            f.dry_run()
