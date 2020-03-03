import time

import numpy as np
from jina.drivers.helper import array2blob
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
            c.embedding.CopyFrom(array2blob(np.random.random([embed_dim])))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d


class MyTestCase(JinaTestCase):

    def setUp(self) -> None:
        super().setUp()
        import docker
        self.container_name = 'jina/mwu-encoder'
        client = docker.from_env()
        client.images.build(path='mwu-encoder/', tag=self.container_name)

    def test_simple_container(self):
        args = set_pea_parser().parse_args(['--image', self.container_name])
        print(args)

        with ContainerizedPea(args) as cp:
            time.sleep(5)

    def test_flow_container(self):
        f = (Flow()
             .add(name='dummyEncoder', image=self.container_name))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)
