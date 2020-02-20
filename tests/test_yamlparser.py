import os

from jina.helper import yaml, expand_dict
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
