import pathlib

from daemon.models import DaemonID
from daemon.models.base import StoreItem
from daemon.stores.base import BaseStore
from daemon import __root_workspace__


store_items = {
    DaemonID(f'jflow'): StoreItem(),
    DaemonID(f'jflow'): StoreItem(),
    DaemonID(f'jflow'): StoreItem(),
}


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
