import os

from jina.executors import BaseExecutor
from jina.executors.metas import fill_metas_with_defaults
from jina.helper import yaml, expand_dict
from jina.main.parser import set_pea_parser
from jina.peapods.pea import BasePea
from pkg_resources import resource_filename
from tests import JinaTestCase


cur_dir = os.path.dirname(os.path.abspath(__file__))


class MyTestCase(JinaTestCase):

    def test_yaml_expand(self):
        with open(os.path.join(cur_dir, 'yaml/test-expand.yml')) as fp:
            a = yaml.load(fp)
        b = expand_dict(a)
        print(b)

    def test_yaml_expand2(self):
        with open(os.path.join(cur_dir, 'yaml/test-expand2.yml')) as fp:
            a = yaml.load(fp)
        os.environ['ENV1'] = 'a'
        b = expand_dict(a)
        assert b['components'][0]['metas']['bad_var'] == 'real-compound'
        assert b['components'][1]['metas']['bad_var'] == 2
        assert b['components'][1]['metas']['float_var'] == 0.232
        assert b['components'][1]['metas']['mixed'] == '0.232-2-real-compound'
        assert b['components'][1]['metas']['mixed_env'] == '0.232-a'
        assert b['components'][1]['metas']['name_shortcut'] == 'test_numpy'

    def test_yaml_expand3(self):
        with open(os.path.join(cur_dir, 'yaml/test-expand3.yml')) as fp:
            a = yaml.load(fp)
        b = expand_dict(a)
        print(b)

    def test_attr_dict(self):
        class AttrDict:
            pass

        a = AttrDict()
        a.__dict__['sda'] = 1
        assert a.sda == 1
        a.__dict__['components'] = list()
        self.assertTrue(isinstance(a.components, list))

    def test_yaml_fill(self):
        with open(os.path.join(cur_dir, 'yaml/test-expand2.yml')) as fp:
            a = yaml.load(fp)
        print(fill_metas_with_defaults(a))

    def test_class_yaml(self):
        class DummyClass:
            pass

        yaml.register_class(DummyClass)

        a = yaml.load('!DummyClass {}')
        assert type(a) == DummyClass

        with open(resource_filename('jina',
                                    '/'.join(('resources', 'executors.requests.%s.yml' % 'BaseExecutor')))) as fp:
            b = fp.read()
            print(b)
            c = yaml.load(b)
            print(c)

        args = set_pea_parser().parse_args([])

        with BasePea(args) as p:
            pass

        from jina.executors.requests import _defaults
        self.assertIsNotNone(_defaults)

    def test_joint_indexer(self):
        b = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-joint.yml'))
        print(b[0].name)
        print(type(b[0]))
        print(b._drivers['SearchRequest'][0]._executor_name)
        print(b._drivers['SearchRequest'])
        b.attach(pea=None)
        assert b._drivers['SearchRequest'][0]._exec == b[0]
        assert b._drivers['SearchRequest'][-1]._exec == b[1]
