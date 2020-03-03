import unittest

from jina.drivers import BaseDriver
from jina.drivers.control import ControlReqDriver
from jina.drivers.search import MetaDocSearchDriver
from jina.executors import BaseExecutor
from jina.helper import yaml
from pkg_resources import resource_filename
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_load_yaml1(self):
        with open('yaml/test-driver.yml', encoding='utf8') as fp:
            a = yaml.load(fp)

        self.assertTrue(isinstance(a[0], MetaDocSearchDriver))
        self.assertTrue(isinstance(a[1], ControlReqDriver))
        self.assertTrue(isinstance(a[2], BaseDriver))

        with open('test_driver.yml', 'w', encoding='utf8') as fp:
            yaml.dump(a[0], fp)

        with open('test_driver.yml', encoding='utf8') as fp:
            b = yaml.load(fp)

        self.assertTrue(isinstance(b, MetaDocSearchDriver))
        self.assertEqual(b._executor_name, a[0]._executor_name)

        self.add_tmpfile('test_driver.yml')

    def test_load_yaml2(self):
        a = BaseExecutor.load_config('yaml/test-exec-with-driver.yml')
        a.save_config()
        p = a.config_abspath
        b = BaseExecutor.load_config(p)
        self.assertEqual(a._drivers, b._drivers)
        self.add_tmpfile(p)
        a.touch()
        a.save()
        c = BaseExecutor.load(a.save_abspath)
        self.assertEqual(a._drivers, c._drivers)
        self.add_tmpfile(a.save_abspath)

    def test_resource_executor(self):
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors.route.yml'))))
        self.assertEqual(a.name, 'route')
        self.assertEqual(len(a._drivers), 4)
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors.merge.yml'))))
        self.assertEqual(a.name, 'merge')
        self.assertEqual(len(a._drivers), 4)
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors.clear.yml'))))
        self.assertEqual(a.name, 'clear')
        self.assertEqual(len(a._drivers), 4)

    def test_multiple_executor(self):
        from jina.executors.encoders import BaseEncoder
        from jina.executors.indexers import BaseIndexer
        from jina.executors.rankers import BaseRanker
        from jina.executors.transformers import BaseDocTransformer
        from jina.executors.transformers import BaseChunkTransformer

        class D1(BaseEncoder):
            pass

        d1 = D1()
        self.assertEqual(len(d1._drivers), 4)

        class D2(BaseIndexer):
            pass

        d2 = D2('dummy.bin')
        self.assertEqual(len(d2._drivers), 1)

        class D3(BaseRanker):
            pass

        d3 = D3()
        self.assertEqual(len(d3._drivers), 2)

        class D4(BaseDocTransformer):
            pass

        d4 = D4()
        self.assertEqual(len(d4._drivers), 4)

        class D5(BaseChunkTransformer):
            pass

        d5 = D5()
        self.assertEqual(len(d5._drivers), 4)


if __name__ == '__main__':
    unittest.main()
