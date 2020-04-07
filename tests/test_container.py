import os
import time

from jina.flow import Flow
from jina.main.checker import NetworkChecker
from jina.main.parser import set_pea_parser, set_ping_parser
from jina.peapods.container import ContainerPea
from jina.peapods.pea import BasePea
from jina.proto import jina_pb2
from tests import JinaTestCase


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


def build_image():
    if not built:
        import docker
        client = docker.from_env()
        print(os.path.dirname(__file__))
        client.images.build(path='mwu-encoder/', tag=img_name)
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
                                            '--yaml-path', './mwu-encoder/mwu_encoder_ext.yml'])
        print(args)

        with ContainerPea(args):
            time.sleep(2)

    def test_flow_with_one_container_pod(self):
        f = (Flow()
             .add(name='dummyEncoder', image=img_name))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_with_one_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder', image=img_name, yaml_path='./mwu-encoder/mwu_encoder_ext.yml'))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_with_replica_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder',
                  image=img_name,
                  yaml_path='./mwu-encoder/mwu_encoder_ext.yml',
                  replicas=3))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)
            fl.index(raw_bytes=random_docs(10), in_proto=True)
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_topo1(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:devel', yaml_path='_logroute', entrypoint='jina pod')
             .add(name='d2', image='jinaai/jina:devel', yaml_path='_logroute', entrypoint='jina pod')
             .add(name='d3', image='jinaai/jina:devel', yaml_path='_logroute',
                  needs='d1', entrypoint='jina pod')
             .join(['d3', 'd2']))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_topo_mixed(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:devel', yaml_path='_logroute', entrypoint='jina pod')
             .add(name='d2', yaml_path='_logroute')
             .add(name='d3', image='jinaai/jina:devel', yaml_path='_logroute',
                  needs='d1', entrypoint='jina pod')
             .join(['d3', 'd2'])
             )

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_topo_replicas(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:devel', entrypoint='jina pod', yaml_path='_forward', replicas=3)
             .add(name='d2', yaml_path='_forward', replicas=3)
             .add(name='d3', image='jinaai/jina:devel', entrypoint='jina pod', yaml_path='_forward',
                  needs='d1')
             .join(['d3', 'd2'])
             )

        with f.build() as fl:
            fl.dry_run()
            fl.index(raw_bytes=random_docs(1000), in_proto=True)

    def test_container_volume(self):
        f = (Flow()
             .add(name='dummyEncoder', image=img_name, volumes='./abc', yaml_path='mwu-encoder/mwu_encoder_upd.yml'))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

        out_file = './abc/ext-mwu-encoder.bin'
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
