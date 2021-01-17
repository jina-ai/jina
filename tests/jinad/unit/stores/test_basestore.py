import pytest

from daemon.stores.base import BaseStore

store_items = {
    '123': {'object': 'abc'},
    '456': {'object': 'hij'},
    '789': {}
}


def test_base_store_clear():
    s = BaseStore()
    old_update = s._last_update
    assert s._last_update
    s._items.update(store_items)
    assert len(s) == 3
    s.clear()
    assert len(s) == 0
    assert old_update < s._last_update


def test_base_store_del():
    s = BaseStore()
    old_update = s._last_update
    assert s._last_update
    s._items.update(store_items)
    assert len(s) == 3
    del s['789']
    assert len(s) == 2
    s.pop('123')
    assert len(s) == 1
    assert old_update < s._last_update

    old_update = s._last_update
    with pytest.raises(KeyError):
        del s['12345']
    assert old_update == s._last_update
