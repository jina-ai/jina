import os

import pytest

from jina.executors import BaseExecutor
from jina.executors.compound import CompoundExecutor
from tests import rm_files

cur_dir = os.path.dirname(os.path.abspath(__file__))


class DummyA(BaseExecutor):
    def say(self):
        return 'a'


class DummyB(BaseExecutor):
    def say(self):
        return 'b'


def test_compositional_dump(test_metas):
    a = CompoundExecutor(metas=test_metas)
    a.components = lambda: [BaseExecutor(), BaseExecutor()]
    assert a.name
    a.touch()
    a.save()
    a.save_config()
    assert os.path.exists(a.save_abspath)
    assert os.path.exists(a.config_abspath)
    rm_files([a.save_abspath, a.config_abspath])


@pytest.fixture
def tmp_workspace(tmpdir):
    os.environ['JINA_TEST_COMPOUND_FROM_YAML'] = str(tmpdir)
    yield
    del os.environ['JINA_TEST_COMPOUND_FROM_YAML']


def test_compound_from_yaml(tmp_workspace):
    a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/npvec.yml'))
    assert isinstance(a, CompoundExecutor)
    assert callable(getattr(a, 'add'))
    assert callable(getattr(a, 'query'))
    assert callable(getattr(a, 'meta_add'))
    assert callable(getattr(a, 'meta_query'))
