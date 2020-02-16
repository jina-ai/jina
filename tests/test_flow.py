import unittest

from jina.flow import Flow
from jina.helper import yaml
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_simple_flow(self):
        bytes_gen = (b'aaa' for _ in range(10))
        f = (Flow()
             .add(driver='route'))
        with f.build(runtime='thread') as fl:
            fl.index(raw_bytes=bytes_gen)

    def test_load_flow_from_yaml(self):
        with open('yaml/test-flow.yml') as fp:
            a = Flow.load_config(fp)
            print(a)


if __name__ == '__main__':
    unittest.main()
