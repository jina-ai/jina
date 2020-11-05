import os

from pkg_resources import resource_filename

from jina.executors import BaseExecutor
from jina.executors.metas import fill_metas_with_defaults
from jina.helper import yaml, expand_dict
from jina.parser import set_pea_parser
from jina.peapods.pea import BasePea

cur_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['TEST_WORKDIR'] = os.getcwd()


def test_yaml_expand():
    with open(os.path.join(cur_dir, 'yaml/test-expand.yml')) as fp:
        a = yaml.load(fp)
    b = expand_dict(a)
    assert b['quote_dict'] == {}
    assert b['quote_string'].startswith('{')
    assert b['quote_string'].endswith('}')
    assert b['nest']['quote_dict'] == {}
    assert b['nest']['quote_string'].startswith('{')
    assert b['nest']['quote_string'].endswith('}')
    assert b['exist_env'] != '$PATH'
    assert b['non_exist_env'] == '$JINA_WHATEVER_ENV'


def test_yaml_expand2():
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


def test_yaml_expand3():
    with open(os.path.join(cur_dir, 'yaml/test-expand3.yml')) as fp:
        a = yaml.load(fp)
    b = expand_dict(a)
    assert b['pea_workspace'] != '{root.workspace}/{root.name}-{this.pea_id}'


def test_attr_dict():
    class AttrDict:
        pass

    a = AttrDict()
    a.__dict__['sda'] = 1
    assert a.sda == 1
    a.__dict__['components'] = list()
    assert isinstance(a.components, list)


def test_yaml_fill():
    with open(os.path.join(cur_dir, 'yaml/test-expand2.yml')) as fp:
        a = yaml.load(fp)
    print(fill_metas_with_defaults(a))


def test_class_yaml():
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

    with BasePea(args):
        pass

    from jina.executors.requests import _defaults
    assert _defaults is not None


def test_joint_indexer():
    b = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/test-joint.yml'))
    print(b[0].name)
    print(type(b[0]))
    print(b._drivers['SearchRequest'][0]._executor_name)
    print(b._drivers['SearchRequest'])
    b.attach(pea=None)
    assert b._drivers['SearchRequest'][0]._exec == b[0]
    assert b._drivers['SearchRequest'][-1]._exec == b[1]
