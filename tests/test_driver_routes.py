import unittest

from jina.drivers import Driver
from jina.helper import yaml
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_load_yaml1(self):
        with open('yaml/driver_with_routes.yml', encoding='utf8') as fp:
            a = yaml.load(fp)

        d = Driver()
        d.install(a)
        print(d._handlers)


if __name__ == '__main__':
    unittest.main()
