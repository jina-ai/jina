import os
from pathlib import Path

import pytest
import yaml
from pkg_resources import resource_filename

from jina.executors import BaseExecutor
from jina.executors.indexers.vector import NumpyIndexer
from jina.executors.metas import fill_metas_with_defaults
from jina.helper import expand_dict
from jina.helper import expand_env_var
from jina.jaml import JAML
from jina.parser import set_pea_parser
from jina.peapods.peas import BasePea

cur_dir = Path(__file__).parent


@pytest.fixture(scope='function')
def test_workspace(tmpdir):
    os.environ['JINA_TEST_JOINT'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_JOINT']
    yield workspace_path
    del os.environ['JINA_TEST_JOINT']


def test_yaml_expand():
    with open(cur_dir / 'yaml/test-expand.yml') as fp:
        a = JAML.load(fp)
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
    with open(cur_dir / 'yaml/test-expand2.yml') as fp:
        a = JAML.load(fp)
    os.environ['ENV1'] = 'a'
    b = expand_dict(a)
    assert b['components'][0]['metas']['bad_var'] == 'real-compound'
    assert b['components'][1]['metas']['bad_var'] == 2
    assert b['components'][1]['metas']['float_var'] == 0.232
    assert b['components'][1]['metas']['mixed'] == '0.232-2-real-compound'
    assert b['components'][1]['metas']['mixed_env'] == '0.232-a'
    assert b['components'][1]['metas']['name_shortcut'] == 'test_numpy'


def test_yaml_expand3():
    with open(cur_dir / 'yaml/test-expand3.yml') as fp:
        a = JAML.load(fp)

    b = expand_dict(a)
    assert b['max_snapshot'] == 0
    assert b['pea_workspace'] != '{root.workspace}/{root.name}-{this.pea_id}'


def test_yaml_expand4():
    os.environ['ENV1'] = 'a'
    with open(cur_dir / 'yaml/test-expand4.yml') as fp:
        b = JAML.load(fp, substitute=True,
                      context={'context_var': 3.14,
                               'context_var2': 'hello-world'})

    assert b['components'][0]['metas']['bad_var'] == 'real-compound'
    assert b['components'][1]['metas']['bad_var'] == 2
    assert b['components'][1]['metas']['float_var'] == 0.232
    assert b['components'][1]['metas']['mixed'] == '0.232-2-real-compound'
    assert b['components'][1]['metas']['name_shortcut'] == 'test_numpy'
    assert b['components'][1]['metas']['mixed_env'] == '0.232-a'
    assert b['components'][1]['metas']['random_id'] == 3.14
    assert b['components'][1]['metas']['config_str'] == 'hello-world'


def test_attr_dict():
    class AttrDict:
        pass

    a = AttrDict()
    a.__dict__['sda'] = 1
    assert a.sda == 1
    a.__dict__['components'] = list()
    assert isinstance(a.components, list)


def test_yaml_fill():
    with open(cur_dir / 'yaml/test-expand2.yml') as fp:
        a = JAML.load(fp)
    print(fill_metas_with_defaults(a))


def test_class_yaml():
    class DummyClass:
        pass

    JAML.register(DummyClass)

    a = JAML.load('!DummyClass {}')
    assert type(a) == DummyClass

    with open(resource_filename('jina',
                                '/'.join(('resources', 'executors.requests.BaseExecutor.yml')))) as fp:
        b = fp.read()
        print(b)
        c = JAML.load(b)
        print(c)

    args = set_pea_parser().parse_args([])

    with BasePea(args):
        pass

    from jina.executors.requests import _defaults
    assert _defaults is not None


def test_joint_indexer(test_workspace):
    b = BaseExecutor.load_config(str(cur_dir / 'yaml/test-joint.yml'))
    b.attach(pea=None)
    assert b._drivers['SearchRequest'][0]._exec == b[0]
    assert b._drivers['SearchRequest'][-1]._exec == b[1]


@pytest.mark.parametrize(
    'yaml_dir, executor',
    [
        ('yaml/dummy_exec1.yml', BaseExecutor),
        ('yaml/dummy_exec2.yml', NumpyIndexer)
    ]
)
def test_load_yaml(yaml_dir, executor, tmpdir):
    with executor.load_config(yaml_dir) as e:
        e.save(tmpdir.join(e.save_abspath))
        e.save_config(tmpdir.join(e.config_abspath))


def test_load_external_fail():
    with pytest.raises(yaml.constructor.ConstructorError):
        BaseExecutor.load_config('yaml/dummy_ext_exec.yml')


def test_load_external_success():
    with BaseExecutor.load_config('yaml/dummy_ext_exec_success.yml') as e:
        assert e.__class__.__name__ == 'DummyExternalIndexer'


def test_expand_env():
    assert expand_env_var('$PATH-${AA}') != '$PATH-${AA}'
