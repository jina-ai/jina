import pickle

import pytest

from jina.types.mixin import ProtoTypeMixin


@pytest.mark.parametrize('cls', ProtoTypeMixin.__subclasses__())
def test_pickle_dump_load(cls):
    r = pickle.loads(pickle.dumps(cls()))
    isinstance(r, cls)
