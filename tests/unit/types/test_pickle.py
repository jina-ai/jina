import pickle

import pytest

from jina import DocumentArray, DocumentArrayMemmap
from jina.types.mixin import ProtoTypeMixin
from jina.types.request import Request
from jina.types.request.data import DataRequest


@pytest.mark.parametrize('cls', ProtoTypeMixin.__subclasses__())
def test_pickle_dump_load(cls):
    # Request class is abstract, rather use DataRequest
    if cls == Request:
        cls = DataRequest
    r = pickle.loads(pickle.dumps(cls()))
    isinstance(r, cls)


@pytest.mark.parametrize('cls', [DocumentArray, DocumentArrayMemmap])
def test_pickle_da_dam(cls):
    da = cls.empty(531)
    r = pickle.loads(pickle.dumps(da))
    isinstance(r, cls)
    assert len(da) == 531
