import os
import time

import docker

from jina.flow import Flow
from jina.main.parser import set_pea_parser
from jina.peapods.pea import ContainerizedPea
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


container_name = 'jina/mwu-encoder'
client = docker.from_env()

print(os.path.dirname(__file__))
client.images.build(path='mwu-encoder/', tag=container_name)
client.close()


class MyTestCase(JinaTestCase):

    def tearDown(self) -> None:
        super().tearDown()
        time.sleep(2)

    def test_simple_container(self):
        args = set_pea_parser().parse_args(['--image', container_name])
        print(args)

        with ContainerizedPea(args) as cp:
            time.sleep(2)

    def test_simple_container_with_ext_yaml(self):
        args = set_pea_parser().parse_args(['--image', container_name,
                                            '--yaml_path', './mwu-encoder/mwu_encoder_ext.yml'])
        print(args)

        with ContainerizedPea(args) as cp:
            time.sleep(2)

    def test_flow_no_container(self):
        f = (Flow()
             .add(name='dummyEncoder', yaml_path='mwu-encoder/mwu_encoder.yml'))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)

    def test_flow_with_container(self):
        f = (Flow()
             .add(name='dummyEncoder', image=container_name))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)

    def test_flow_with_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder', image=container_name, yaml_path='./mwu-encoder/mwu_encoder_ext.yml'))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)

    def test_flow_with_replica_container_ext_yaml(self):
        f = (Flow()
             .add(name='dummyEncoder',
                  image=container_name,
                  yaml_path='./mwu-encoder/mwu_encoder_ext.yml',
                  replicas=3))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)
            fl.index(raw_bytes=random_docs(10), in_proto=True, callback=print)
