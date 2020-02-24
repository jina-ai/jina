import unittest

from jina.drivers import BaseDriver
from jina.drivers.control import ControlReqDriver
from jina.drivers.search import DocMetaSearchDriver
from jina.helper import yaml
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_load_yaml1(self):
        with open('yaml/test-driver.yml', encoding='utf8') as fp:
            a = yaml.load(fp)

        self.assertTrue(isinstance(a[0], DocMetaSearchDriver))
        self.assertTrue(isinstance(a[1], ControlReqDriver))
        self.assertTrue(isinstance(a[2], BaseDriver))

        with open('test_driver.yml', 'w', encoding='utf8') as fp:
            yaml.dump(a[0], fp)

        with open('test_driver.yml', encoding='utf8') as fp:
            b = yaml.load(fp)

        self.assertTrue(isinstance(b, DocMetaSearchDriver))
        self.assertEqual(b._executor_name, a[0]._executor_name)

        self.add_tmpfile('test_driver.yml')


if __name__ == '__main__':
    unittest.main()
