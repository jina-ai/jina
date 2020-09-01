import pytest

from jina.executors import BaseExecutor
from jina.executors.indexers import BaseIndexer
# BaseIndexer is already registered
from jina.helper import yaml

assert 'BaseIndexer' in BaseExecutor._registered_class

# init from YAML should be okay as well
BaseExecutor.load_config('BaseIndexer')

BaseIndexer().save_config('tmp.yml')
with open('tmp.yml') as fp:
    s = yaml.load(fp)


def assert_bi():
    b = BaseIndexer(1)
    b.save_config('tmp.yml')
    with open('tmp.yml') as fp:
        b = yaml.load(fp)
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
