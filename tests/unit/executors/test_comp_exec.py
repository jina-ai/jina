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


def test_compositional_route(monkeypatch, test_metas):
    monkeypatch.setattr(BaseExecutor, 'exec_methods', ['say'])
    da = DummyA()
    db = DummyB()
    a = CompoundExecutor(metas=test_metas)

    a.components = lambda: [da, db]
    assert a.say_all() == ['a', 'b']
    with pytest.raises(AttributeError):
        a.say()

    b = CompoundExecutor({'say': {da.name: 'say'}}, metas=test_metas)
    b.components = lambda: [da, db]
    assert b.say_all() == ['a', 'b']
    assert b.say() == 'a'
    b.add_route('say', db.name, 'say')
    assert b.say() == 'b'
    b.save_config()
    assert os.path.exists(b.config_abspath)

    c = BaseExecutor.load_config(b.config_abspath)
    assert c.say_all() == ['a', 'b']
    assert c.say() == 'a'

    b.add_route('say', db.name, 'say', is_stored=True)
    b.save_config()
    c = BaseExecutor.load_config(b.config_abspath)
    assert c.say_all() == ['a', 'b']
    assert c.say() == 'b'

    b.touch()
    b.save()
    assert os.path.exists(b.save_abspath)

    d = BaseExecutor.load(b.save_abspath)
    assert d.say_all() == ['a', 'b']
    assert d.say() == 'b'


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
