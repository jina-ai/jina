import pathlib
import uuid

import pytest

from daemon.models import DaemonID
from daemon.models.base import StoreItem
from daemon.stores.base import BaseStore
from jina.helper import random_identity, random_uuid
from daemon import __root_workspace__

keys = [DaemonID(f'jflow-{uuid.UUID(random_identity())}') for _ in range(3)]


store_items = {keys[0]: StoreItem(), keys[1]: StoreItem(), keys[2]: StoreItem()}


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


class DummyStore(BaseStore):
    def __init__(self, mock):
        super().__init__()
        self.some_field = 'hello world'
        self.mock = mock

    @BaseStore.dump
    def some_function(self):
        self.mock()


def test_base_store_serialization(mocker):
    mock = mocker.Mock()
    pathlib.Path(__root_workspace__).mkdir(parents=True, exist_ok=True)

    dummy_store = DummyStore(mock)
    dummy_store.status.items.update(store_items)
    dummy_store.some_function()
    loaded_store = DummyStore.load()

    assert loaded_store == dummy_store
    mock.assert_called()
