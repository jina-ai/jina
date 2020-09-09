import os
import shutil
import pytest

from jina.executors import BaseExecutor
from jina.executors.compound import CompoundExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)


class DummyA(BaseExecutor):
    def say(self):
        return 'a'


class DummyB(BaseExecutor):
    def say(self):
        return 'b'


def test_compositional_route():
    da = DummyA()
    db = DummyB()
    a = CompoundExecutor()

    a.components = lambda: [da, db]
    assert a.say_all() == ['a', 'b']
    with pytest.raises(AttributeError):
        a.say()

    b = CompoundExecutor({'say': {da.name: 'say'}})
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

    rm_files([b.save_abspath, b.config_abspath])


def test_compositional_dump():
    a = CompoundExecutor()
    a.components = lambda: [BaseExecutor(), BaseExecutor()]
    assert a.name
    a.touch()
    a.save()
    a.save_config()
    assert os.path.exists(a.save_abspath)
    assert os.path.exists(a.config_abspath)
    rm_files([a.save_abspath, a.config_abspath])


def test_compound_from_yaml():
    a = BaseExecutor.load_config(os.path.join(cur_dir, 'yaml/npvec.yml'))
    assert isinstance(a, CompoundExecutor)
    assert callable(getattr(a, 'add'))
    assert callable(getattr(a, 'query'))
    assert callable(getattr(a, 'meta_add'))
    assert callable(getattr(a, 'meta_query'))
    rm_files([c.index_abspath for c in a.components])
    rm_files(['test-workspace'])
