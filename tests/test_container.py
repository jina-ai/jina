import os
import time

import docker

from jina.flow import Flow
from jina.main.checker import NetworkChecker
from jina.main.parser import set_pea_parser, set_pod_parser, set_ping_parser
from jina.peapods.pea import ContainerPea, Pea
from jina.peapods.pod import Pod
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


img_name = 'jina/mwu-encoder'
client = docker.from_env()

print(os.path.dirname(__file__))
client.images.build(path='mwu-encoder/', tag=img_name)
client.close()


class MyTestCase(JinaTestCase):

    def tearDown(self) -> None:
        super().tearDown()
        time.sleep(2)

    def test_pod_status(self):
        args = set_pod_parser().parse_args(['--replicas', '3'])
        with Pod(args) as p:
            self.assertEqual(len(p.status), p.num_peas)
            for v in p.status:
                self.assertIsNotNone(v)

    def test_simple_container(self):
        args = set_pea_parser().parse_args(['--image', img_name])
        print(args)

        with ContainerPea(args) as cp:
            time.sleep(2)

    def test_simple_container_with_ext_yaml(self):
        args = set_pea_parser().parse_args(['--image', img_name,
                                            '--yaml_path', './mwu-encoder/mwu_encoder_ext.yml'])
        print(args)

        with ContainerPea(args) as cp:
            time.sleep(2)

    def test_flow_no_container(self):
        f = (Flow()
             .add(name='dummyEncoder', yaml_path='mwu-encoder/mwu_encoder.yml'))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_with_container(self):
        f = (Flow()
             .add(name='dummyEncoder', image=img_name))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_with_container_ext_yaml(self):
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
             .add(name='d1', image='jinaai/jina:master-debian', yaml_path='logroute', entrypoint='jina pod')
             .add(name='d2', image='jinaai/jina:master-debian', yaml_path='logroute', entrypoint='jina pod')
             .add(name='d3', image='jinaai/jina:master-debian', yaml_path='logroute',
                  recv_from='d1', entrypoint='jina pod')
             .join(['d3', 'd2'])
             )

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_topo_mixed(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:master-debian', yaml_path='logroute', entrypoint='jina pod')
             .add(name='d2', yaml_path='logroute')
             .add(name='d3', image='jinaai/jina:master-debian', yaml_path='logroute',
                  recv_from='d1', entrypoint='jina pod')
             .join(['d3', 'd2'])
             )

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)

    def test_flow_topo_replicas(self):
        f = (Flow()
             .add(name='d1', image='jinaai/jina:master-debian', entrypoint='jina pod', yaml_path='route', replicas=3)
             .add(name='d2', yaml_path='route', replicas=3)
             .add(name='d3', image='jinaai/jina:master-debian', entrypoint='jina pod', yaml_path='route',
                  recv_from='d1')
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

    def test_ping(self):
        a1 = set_pea_parser().parse_args([])
        a2 = set_ping_parser().parse_args(['0.0.0.0', str(a1.port_ctrl), '--print_response'])
        a3 = set_ping_parser().parse_args(['0.0.0.1', str(a1.port_ctrl), '--timeout', '1000'])
        a4 = set_pea_parser().parse_args(['--image', img_name])
        a5 = set_ping_parser().parse_args(['0.0.0.0', str(a4.port_ctrl), '--print_response'])

        with self.assertRaises(SystemExit) as cm:
            with Pea(a1):
                NetworkChecker(a2)

        self.assertEqual(cm.exception.code, 0)

        # test with bad addresss
        with self.assertRaises(SystemExit) as cm:
            with Pea(a1):
                NetworkChecker(a3)

        self.assertEqual(cm.exception.code, 1)

        # test with container
        with self.assertRaises(SystemExit) as cm:
            with Pea(a4):
                NetworkChecker(a5)

        self.assertEqual(cm.exception.code, 0)

    def test_dryrun(self):
        f = (Flow()
             .add(name='dummyEncoder', yaml_path='mwu-encoder/mwu_encoder.yml'))

        with f.build() as fl:
            fl.dry_run()