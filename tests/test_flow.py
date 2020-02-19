import unittest

from jina.flow import Flow
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_simple_flow(self):
        bytes_gen = (b'aaa' for _ in range(10))
        f = (Flow()
             .add(driver_group='route'))
        with f.build(runtime='thread') as fl:
            fl.index(raw_bytes=bytes_gen)

    def test_load_flow_from_yaml(self):
        with open('yaml/test-flow.yml') as fp:
            a = Flow.load_config(fp)
            with open('yaml/swarm-out.yml', 'w') as fp, a as fl:
                fl.to_swarm_yaml(fp)
            self.add_tmpfile('yaml/swarm-out.yml')

    def test_flow_identical(self):
        with open('yaml/test-flow.yml') as fp:
            a = Flow.load_config(fp)

        b = (Flow(driver_yaml_path='', sse_logger=True)
             .add(name='chunk_seg', driver_group='segment', replicas=3)
             .add(name='encode1', driver_group='index-meta-doc', replicas=2)
             .add(name='encode2', driver_group='index-meta-doc', replicas=2, recv_from='chunk_seg')
             .join(['encode1', 'encode2'])
             )

        self.assertEqual(a, b)


if __name__ == '__main__':
    unittest.main()
