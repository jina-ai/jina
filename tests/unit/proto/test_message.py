import pytest

from jina.clients.python.request import _generate
from jina.proto.message import LazyRequest, _trigger_fields
from tests import random_docs


@pytest.mark.parametrize('field', _trigger_fields.difference({'command', 'args', 'flush'}))
def test_lazy_access(field):
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.was_read

        # access r.train
        print(getattr(r, field))

        # now it is read
        assert r.was_read


def test_lazy_nest_access():
    reqs = (LazyRequest(r.SerializeToString(), False) for r in _generate(random_docs(10)))
    for r in reqs:
        assert not r.was_read

        # access r.train
        print(r.docs[0].id)

        # now it is read
        assert r.was_read
