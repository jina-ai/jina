import pytest
import ruamel.yaml

from jina.executors import BaseExecutor
from jina.executors.indexers.vector import NumpyIndexer
from jina.helper import expand_env_var


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
    with pytest.raises(ruamel.yaml.constructor.ConstructorError):
        BaseExecutor.load_config('yaml/dummy_ext_exec.yml')


def test_load_external_success():
    with BaseExecutor.load_config('yaml/dummy_ext_exec_success.yml') as e:
        assert e.__class__.__name__ == 'DummyExternalIndexer'


def test_expand_env():
    assert expand_env_var('$PATH-${AA}') != '$PATH-${AA}'
