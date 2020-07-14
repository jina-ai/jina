import unittest
import os

from jina.drivers import BaseDriver
from jina.drivers.control import ControlReqDriver
from jina.drivers.search import KVSearchDriver
from jina.executors import BaseExecutor
from jina.helper import yaml
from jina.main.parser import set_pod_parser
from jina.peapods import Pod
from pkg_resources import resource_filename
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    def test_load_yaml1(self):
        with open(os.path.join(cur_dir, 'yaml/test-driver.yml'), encoding='utf8') as fp:
            a = yaml.load(fp)

        self.assertTrue(isinstance(a[0], KVSearchDriver))
        self.assertTrue(isinstance(a[1], ControlReqDriver))
        self.assertTrue(isinstance(a[2], BaseDriver))

        with open('test_driver.yml', 'w', encoding='utf8') as fp:
            yaml.dump(a[0], fp)

        with open('test_driver.yml', encoding='utf8') as fp:
            b = yaml.load(fp)

        self.assertTrue(isinstance(b, KVSearchDriver))
        self.assertEqual(b._executor_name, a[0]._executor_name)

        self.add_tmpfile('test_driver.yml')

    def test_load_cust_with_driver(self):
        a = BaseExecutor.load_config(os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml'))
        self.assertEqual(a._drivers['ControlRequest'][0].__class__.__name__, 'MyAwesomeDriver')
        p = set_pod_parser().parse_args(['--yaml-path', os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml')])
        with Pod(p):
            # will print a cust msg from the driver when terminate
            pass

    def test_pod_new_api_from_kwargs(self):
        a = BaseExecutor.load_config(os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml'))
        self.assertEqual(a._drivers['ControlRequest'][0].__class__.__name__, 'MyAwesomeDriver')

        with Pod(yaml_path=os.path.join(cur_dir, 'mwu-encoder/mwu_encoder_driver.yml')):
            # will print a cust msg from the driver when terminate
            pass

    def test_load_yaml2(self):
        a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-exec-with-driver.yml'))
        self.assertEqual(len(a._drivers), 2)
        # should be able to auto fill in ControlRequest
        self.assertTrue('ControlRequest' in a._drivers)
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
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors._route.yml'))))
        self.assertEqual(a.name, 'route')
        self.assertEqual(len(a._drivers), 4)
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors._forward.yml'))))
        self.assertEqual(a.name, 'forward')
        self.assertEqual(len(a._drivers), 4)
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors._merge.yml'))))
        self.assertEqual(a.name, 'merge')
        self.assertEqual(len(a._drivers), 4)
        a = BaseExecutor.load_config(resource_filename('jina', '/'.join(('resources', 'executors._clear.yml'))))
        self.assertEqual(a.name, 'clear')
        self.assertEqual(len(a._drivers), 4)

    def test_multiple_executor(self):
        from jina.executors.encoders import BaseEncoder
        from jina.executors.indexers import BaseIndexer
        from jina.executors.rankers import Chunk2DocRanker
        from jina.executors.crafters import BaseDocCrafter
        from jina.executors.crafters import BaseChunkCrafter

        class D1(BaseEncoder):
            pass

        d1 = D1()
        self.assertEqual(len(d1._drivers), 4)

        class D2(BaseIndexer):
            pass

        d2 = D2('dummy.bin')
        self.assertEqual(len(d2._drivers), 1)

        class D3(Chunk2DocRanker):
            pass

        d3 = D3()
        self.assertEqual(len(d3._drivers), 2)

        class D4(BaseDocCrafter):
            pass

        d4 = D4()
        self.assertEqual(len(d4._drivers), 4)

        class D5(BaseChunkCrafter):
            pass

        d5 = D5()
        self.assertEqual(len(d5._drivers), 4)


if __name__ == '__main__':
    unittest.main()
