import os

import pytest
import yaml

from jina import Deployment, Gateway
from jina.constants import __default_executor__, __default_host__
from jina.helper import expand_dict, expand_env_var
from jina.jaml import JAML
from jina.serve.executors import BaseExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def test_workspace(tmpdir):
    os.environ['JINA_TEST_JOINT'] = str(tmpdir)
    workspace_path = os.environ['JINA_TEST_JOINT']
    yield workspace_path
    del os.environ['JINA_TEST_JOINT']


def test_yaml_expand():
    with open(os.path.join(cur_dir, 'yaml/test-expand.yml')) as fp:
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
    with open(os.path.join(cur_dir, 'yaml/test-expand2.yml')) as fp:
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
    with open(os.path.join(cur_dir, 'yaml/test-expand3.yml')) as fp:
        a = JAML.load(fp)

    b = expand_dict(a)
    assert b['max_snapshot'] == 0


def test_yaml_expand4():
    os.environ['ENV1'] = 'a'
    os.environ['ENV2'] = '{"1": "2"}'

    with open(os.path.join(cur_dir, 'yaml/test-expand4.yml')) as fp:
        b = JAML.load(
            fp,
            substitute=True,
            context={'context_var': 3.14, 'context_var2': 'hello-world'},
        )

    assert b['components'][0]['metas']['bad_var'] == 'real-compound'
    assert b['components'][1]['metas']['bad_var'] == 2
    assert b['components'][1]['metas']['float_var'] == 0.232
    assert b['components'][1]['metas']['mixed'] == '0.232-2-real-compound'
    assert b['components'][1]['metas']['name_shortcut'] == 'test_numpy'
    assert b['components'][1]['metas']['mixed_env'] == '0.232-a'
    assert b['components'][1]['metas']['random_id'] == 3.14
    assert b['components'][1]['metas']['config_str'] == 'hello-world'
    assert b['components'][1]['metas']['bracket_env'] == '{"1": "2"}'
    assert b['components'][1]['metas']['bracket_env'] == '{"1": "2"}'
    assert b['components'][1]['metas']['context_dot'] == 3.14


def test_attr_dict():
    class AttrDict:
        pass

    a = AttrDict()
    a.__dict__['sda'] = 1
    assert a.sda == 1
    a.__dict__['components'] = list()
    assert isinstance(a.components, list)


def test_class_yaml():
    class DummyClass:
        pass

    JAML.register(DummyClass)

    a = JAML.load('!DummyClass {}')
    assert type(a) == DummyClass


def test_load_external_fail():
    with pytest.raises(yaml.constructor.ConstructorError):
        BaseExecutor.load_config('yaml/dummy_ext_exec.yml')


def test_load_external_success():
    with BaseExecutor.load_config('yaml/dummy_ext_exec_success.yml') as e:
        assert e.__class__.__name__ == 'DummyExternalIndexer'


def test_expand_env():
    assert expand_env_var('$PATH-${AA}') != '$PATH-${AA}'


def test_encoder_name_env_replace():
    os.environ['BE_TEST_NAME'] = 'hello123'
    with BaseExecutor.load_config('yaml/test-encoder-env.yml') as be:
        assert be.metas.name == 'hello123'


def test_encoder_name_dict_replace():
    d = {'BE_TEST_NAME': 'hello123'}
    with BaseExecutor.load_config('yaml/test-encoder-env.yml', context=d) as be:
        assert be.metas.name == 'hello123'
        assert be.metas.workspace == 'hello123'


def test_encoder_inject_config_via_kwargs():
    with BaseExecutor.load_config(
        'yaml/test-encoder-env.yml', metas={'shard_id': 345}
    ) as be:
        assert be.metas.shard_id == 345


def test_load_from_dict():
    # !BaseEncoder
    # metas:
    #   name: ${{BE_TEST_NAME}}
    #   batch_size: ${{BATCH_SIZE}}
    #   pod_id: ${{pod_id}}
    #   workspace: ${{this.name}}-${{this.batch_size}}

    d1 = {
        'jtype': __default_executor__,
        'metas': {
            'name': '${{ BE_TEST_NAME }}',
            'workspace': '${{this.name}}',
        },
    }

    # !CompoundExecutor
    # components:
    #   - !BinaryPbIndexer
    #     with:
    #       index_filename: tmp1
    #     metas:
    #       name: test1
    #   - !BinaryPbIndexer
    #     with:
    #       index_filename: tmp2
    #     metas:
    #       name: test2
    # metas:
    #   name: compound1
    d = {'BE_TEST_NAME': 'hello123'}
    b1 = BaseExecutor.load_config(d1, context=d)
    assert isinstance(b1, BaseExecutor)

    assert b1.metas.name == 'hello123'


@pytest.mark.parametrize(
    'yaml_file,gateway_name',
    [
        ('test-custom-gateway.yml', 'DummyGateway'),
        ('test-fastapi-gateway.yml', 'DummyFastAPIGateway'),
    ],
)
def test_load_gateway_external_success(yaml_file, gateway_name):
    with Gateway.load_config(
        f'yaml/{yaml_file}', runtime_args={'port': [12345]}
    ) as gateway:
        assert gateway.__class__.__name__ == gateway_name
        assert gateway.arg1 == 'hello'
        assert gateway.arg2 == 'world'
        assert gateway.arg3 == 'default-arg3'
        assert gateway.runtime_args.timeout_send == 10
        assert gateway.runtime_args.retries == 10
        assert gateway.runtime_args.compression == 'Deflate'
        assert gateway.runtime_args.prefetch == 100


@pytest.mark.parametrize(
    'yaml_file,gateway_name',
    [
        ('test-custom-gateway.yml', 'DummyGateway'),
        ('test-fastapi-gateway.yml', 'DummyFastAPIGateway'),
    ],
)
def test_load_gateway_override_with(yaml_file, gateway_name):
    with Gateway.load_config(
        f'yaml/{yaml_file}',
        uses_with={'arg1': 'arg1', 'arg2': 'arg2', 'arg3': 'arg3'},
        runtime_args={'port': [12345]},
    ) as gateway:
        assert gateway.__class__.__name__ == gateway_name
        assert gateway.arg1 == 'arg1'
        assert gateway.arg2 == 'arg2'
        assert gateway.arg3 == 'arg3'


@pytest.mark.parametrize(
    'yaml_file,expected_replicas,expected_shards,expected_uses',
    [
        ('test-deployment.yml', 2, 3, 'DummyExternalIndexer'),
        ('test-deployment-exec-config.yml', 3, 2, 'dummy_ext_exec_success.yml'),
    ],
)
def test_load_deployment(yaml_file, expected_replicas, expected_shards, expected_uses):
    with Deployment.load_config(os.path.join(cur_dir, f'yaml/{yaml_file}')) as dep:
        assert dep.args.replicas == expected_replicas
        assert dep.args.shards == expected_shards
        assert dep.args.uses == expected_uses
