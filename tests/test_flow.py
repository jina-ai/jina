import unittest

from jina.flow import Flow
from jina.main.checker import NetworkChecker
from jina.main.parser import set_pea_parser, set_ping_parser
from jina.main.parser import set_pod_parser
from jina.peapods.pea import BasePea
from jina.peapods.pod import BasePod
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


class MyTestCase(JinaTestCase):

    def test_ping(self):
        a1 = set_pea_parser().parse_args([])
        a2 = set_ping_parser().parse_args(['0.0.0.0', str(a1.port_ctrl), '--print_response'])
        a3 = set_ping_parser().parse_args(['0.0.0.1', str(a1.port_ctrl), '--timeout', '1000'])

        with self.assertRaises(SystemExit) as cm:
            with BasePea(a1):
                NetworkChecker(a2)

        self.assertEqual(cm.exception.code, 0)

        # test with bad addresss
        with self.assertRaises(SystemExit) as cm:
            with BasePea(a1):
                NetworkChecker(a3)

        self.assertEqual(cm.exception.code, 1)

    def test_simple_flow(self):
        bytes_gen = (b'aaa' for _ in range(10))
        f = (Flow()
             .add(yaml_path='route'))
        with f.build() as fl:
            fl.index(raw_bytes=bytes_gen)

    def test_load_flow_from_yaml(self):
        with open('yaml/test-flow.yml') as fp:
            a = Flow.load_config(fp)
            with open('yaml/swarm-out.yml', 'w') as fp, a.build() as fl:
                fl.to_swarm_yaml(fp)
            self.add_tmpfile('yaml/swarm-out.yml')

    def test_flow_identical(self):
        with open('yaml/test-flow.yml') as fp:
            a = Flow.load_config(fp)

        b = (Flow(sse_logger=False)
             .add(name='chunk_seg', replicas=3)
             .add(name='encode1', replicas=2)
             .add(name='encode2', replicas=2, recv_from='chunk_seg')
             .join(['encode1', 'encode2']))

        self.assertEqual(a, b)

    def test_dryrun(self):
        f = (Flow()
             .add(name='dummyEncoder', yaml_path='mwu-encoder/mwu_encoder.yml'))

        with f.build() as fl:
            fl.dry_run()

    def test_pod_status(self):
        args = set_pod_parser().parse_args(['--replicas', '3'])
        with BasePod(args) as p:
            self.assertEqual(len(p.status), p.num_peas)
            for v in p.status:
                self.assertIsNotNone(v)

    def test_flow_no_container(self):
        f = (Flow()
             .add(name='dummyEncoder', yaml_path='mwu-encoder/mwu_encoder.yml'))

        with f.build() as fl:
            fl.index(raw_bytes=random_docs(10), in_proto=True)


if __name__ == '__main__':
    unittest.main()
