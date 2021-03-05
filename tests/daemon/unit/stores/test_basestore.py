import uuid

import pytest

from daemon.stores.base import BaseStore
from jina.helper import random_identity, random_uuid

keys = [uuid.UUID(random_identity()) for _ in range(3)]


store_items = {keys[0]: {'object': 'abc'}, keys[1]: {'object': 'hij'}, keys[2]: {}}


def test_base_store_clear():
    print(keys)
    s = BaseStore()
    old_update = s._time_updated
    assert s._time_updated
    s._items.update(store_items)
    assert len(s) == 3
    s.clear()
    assert len(s) == 0
    assert old_update < s._time_updated


def test_base_store_del():
    s = BaseStore()
    old_update = s._time_updated
    assert s._time_updated
    s._items.update(store_items)
    assert len(s) == 3
    del s[keys[0]]
    assert len(s) == 2
    s.pop(keys[1])
    assert len(s) == 1
    assert old_update < s._time_updated

    old_update = s._time_updated
    with pytest.raises(KeyError):
        del s[random_uuid()]
    assert old_update == s._time_updated
