import pickle

import pytest

from docarray import DocumentArray, DocumentArrayMemmap
from docarray.base import BaseProtoView
from docarray.simple import NamedScoreMap


@pytest.mark.parametrize('cls', BaseProtoView.__subclasses__())
def test_pickle_dump_load(cls):
    if cls != NamedScoreMap:
        r = pickle.loads(pickle.dumps(cls()))
        isinstance(r, cls)


@pytest.mark.parametrize('cls', [DocumentArray, DocumentArrayMemmap])
def test_pickle_da_dam(cls):
    da = cls.empty(531)
    r = pickle.loads(pickle.dumps(da))
    isinstance(r, cls)
    assert len(da) == 531
