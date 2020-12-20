from pathlib import Path

import pytest

from jina.executors import BaseExecutor
# BaseIndexer is already registered
from jina.jaml import JAML


def test_exec_type(tmpdir):
    tmpdir = Path(tmpdir)
    from jina.executors.indexers import BaseIndexer
    assert 'BaseIndexer' in BaseExecutor._registered_class

    # init from YAML should be okay as well
    BaseExecutor.load_config('BaseIndexer')

    BaseIndexer().save_config(str(tmpdir / 'tmp.yml'))
    with open(tmpdir / 'tmp.yml') as fp:
        s = JAML.load(fp)

    def assert_bi():
        b = BaseIndexer(1)
        b.save_config(str(tmpdir / 'tmp.yml'))
        with open(tmpdir / 'tmp.yml') as fp:
            b = JAML.load(fp)
            assert b.a == 1

    # we override BaseIndexer now, without force it shall not store all init values
    class BaseIndexer(BaseExecutor):

        def __init__(self, a=0):
            super().__init__()
            self.a = a

    with pytest.raises(AssertionError):
        assert_bi()

    class BaseIndexer(BaseExecutor):
        force_register = True

        def __init__(self, a=0):
            super().__init__()
            self.a = a

    assert_bi()
