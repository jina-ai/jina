import os

import pytest

from jina.executors import BaseExecutor

# BaseIndexer is already registered
from jina.jaml import JAML


@pytest.fixture
def unregister():
    from jina.executors.indexers import BaseIndexer

    if 'tests.unit.test_exectype.BaseIndexer' in BaseIndexer._registered_class:
        BaseIndexer._registered_class.remove('tests.unit.test_exectype.BaseIndexer')
    yield
    if 'tests.unit.test_exectype.BaseIndexer' in BaseIndexer._registered_class:
        BaseIndexer._registered_class.remove('tests.unit.test_exectype.BaseIndexer')


@pytest.mark.parametrize('f_register', [True, False])
def test_exec_type(tmpdir, f_register, unregister):
    from jina.executors.indexers import BaseIndexer

    assert 'jina.executors.indexers.BaseIndexer' in BaseExecutor._registered_class

    # init from YAML should be okay as well
    BaseExecutor.load_config('BaseIndexer')

    BaseIndexer().save_config(os.path.join(tmpdir, 'tmp.yml'))
    with open(os.path.join(tmpdir, 'tmp.yml')) as fp:
        _ = JAML.load(fp)

    def assert_bi():
        b = BaseIndexer(1)

        b.save_config(os.path.join(tmpdir, 'tmp.yml'))
        with open(os.path.join(tmpdir, 'tmp.yml')) as fp:
            b = JAML.load(fp)
            assert b.a == 1

    # By this point, BaseIndexer has not registered in reg_cls_set yet and store_init_kwargs will be executed
    class BaseIndexer(BaseExecutor):
        def __init__(self, a=0, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.a = a

    assert_bi()

    class BaseIndexer(BaseExecutor):
        force_register = f_register

        def __init__(self, a=0, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.a = a

    if f_register:
        assert_bi()
    else:
        with pytest.raises(AssertionError):
            assert_bi()
