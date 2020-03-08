import os

from pkg_resources import resource_filename

from jina.executors.metas import fill_metas_with_defaults
from jina.helper import yaml, expand_dict
from jina.main.parser import set_pea_parser
from jina.peapods.pea import Pea
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_yaml_expand(self):
        with open('yaml/test-expand.yml') as fp:
            a = yaml.load(fp)
        b = expand_dict(a)
        print(b)

    def test_yaml_expand2(self):
        with open('yaml/test-expand2.yml') as fp:
            a = yaml.load(fp)
        os.environ['ENV1'] = 'a'
        b = expand_dict(a)
        self.assertEqual(b['components'][0]['metas']['bad_var'], 'real-compound')
        self.assertEqual(b['components'][1]['metas']['bad_var'], 2)
        self.assertEqual(b['components'][1]['metas']['float_var'], 0.232)
        self.assertEqual(b['components'][1]['metas']['mixed'], '0.232-2-real-compound')
        self.assertEqual(b['components'][1]['metas']['mixed_env'], '0.232-a')
        self.assertEqual(b['components'][1]['metas']['name_shortcut'], 'test_numpy')

    def test_yaml_expand3(self):
        with open('yaml/test-expand3.yml') as fp:
            a = yaml.load(fp)
        b = expand_dict(a)
        print(b)

    def test_attr_dict(self):
        class AttrDict:
            pass

        a = AttrDict()
        a.__dict__['sda'] = 1
        self.assertEqual(a.sda, 1)
        a.__dict__['components'] = list()
        self.assertTrue(isinstance(a.components, list))

    def test_yaml_fill(self):
        with open('yaml/test-expand2.yml') as fp:
            a = yaml.load(fp)
        print(fill_metas_with_defaults(a))

    def test_class_yaml(self):
        class DummyClass:
            pass

        yaml.register_class(DummyClass)

        a = yaml.load('!DummyClass {}')
        self.assertEqual(type(a), DummyClass)

        with open(resource_filename('jina',
                                    '/'.join(('resources', 'executors.requests.%s.yml' % 'BaseExecutor')))) as fp:
            b = fp.read()
            print(b)
            c = yaml.load(b)
            print(c)

        args = set_pea_parser().parse_args([])

        with Pea(args) as p:
            pass

        from jina.executors.requests import _defaults
        self.assertIsNotNone(_defaults)
