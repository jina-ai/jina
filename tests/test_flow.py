import unittest

from jina.flow import Flow
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_simple_flow(self):
        bytes_gen = (b'aaa' for _ in range(10))
        f = (Flow()
             .add(driver='route'))
        with f.build(runtime='thread') as fl:
            fl.index(raw_bytes=bytes_gen)


if __name__ == '__main__':
    unittest.main()
