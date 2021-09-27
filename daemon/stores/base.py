import os
import pickle
import shutil
from pathlib import Path
from datetime import datetime
from collections.abc import MutableMapping
from typing import Callable, Dict, Sequence, TYPE_CHECKING, Tuple, Union

from jina.logging.logger import JinaLogger
from .. import jinad_args, __root_workspace__
from ..models import DaemonID
from ..models.base import StoreItem, StoreStatus

if TYPE_CHECKING:
    from ..models.workspaces import WorkspaceItem
    from ..models.containers import ContainerItem


class BaseStore(MutableMapping):
    """The Base class for Daemon stores"""

    _kind = ''
    _status_model = StoreStatus

    def __init__(self):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self.status = self.__class__._status_model()

    def add(self, *args, **kwargs) -> DaemonID:
        """Add a new element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def update(self, *args, **kwargs) -> DaemonID:
        """Updates the element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def delete(self, *args, **kwargs) -> DaemonID:
        """Deletes an element from the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def clear(self) -> None:
        """Deletes an element from the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def __iter__(self):
        return iter(self.status.items)

    def __len__(self):
        return len(self.status.items)

    def __repr__(self) -> str:
        return str(self.status.dict())

    def keys(self) -> Sequence['DaemonID']:
        """Get keys in the store

        :return: Keys in the local store
        """

        return self.status.items.keys()

    def values(self) -> Sequence[Union['WorkspaceItem', 'ContainerItem']]:
        """Get values in the store

        :return: Values in the local store
        """

        return self.status.items.values()

    def items(
        self,
    ) -> Sequence[Tuple['DaemonID', Union['WorkspaceItem', 'ContainerItem']]]:
        """Get items in the store

        :return: Items in the local store
        """

        return self.status.items.items()

    def __getitem__(self, key: DaemonID) -> Union['WorkspaceItem', 'ContainerItem']:
        """Fetch a Container/Workspace object from the store

        :param key: the key (DaemonID) of the object
        :return: the value of the object
        """
        return self.status.items[key]

    def __setitem__(self, key: DaemonID, value: StoreItem) -> None:
        """Add a Container/Workspace object to the store

        :param key: the key (DaemonID) of the object
        :param value: the value to be assigned
        """
        self.status.items[key] = value
        self.status.num_add += 1
        self.status.time_updated = datetime.now()

    def __delitem__(self, key: DaemonID) -> None:
        """Release a Container/Workspace object from the store

        :param key: the key (DaemonID) of the object


        .. #noqa: DAR201"""
        self.status.items.pop(key)
        self.status.num_del += 1
        self.status.time_updated = datetime.now()

    def __setstate__(self, state: Dict):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        now = datetime.now()
        self.status = self._status_model(**state)
        self.status.time_updated = now

    def __getstate__(self) -> Dict:
        return self.status.dict()

    @classmethod
    def dump(cls, func) -> Callable:
        """Dump store as a pickle to local workspace

        :param func: function to be wrapped
        :return: decorator for dump
        """

        def wrapper(self, *args, **kwargs):
            r = func(self, *args, **kwargs)
            filepath = os.path.join(__root_workspace__, f'{self._kind}.store')
            if Path(filepath).is_file():
                shutil.copyfile(filepath, f'{filepath}.backup')
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            return r

        return wrapper

    @classmethod
    def load(cls) -> 'BaseStore':
        """Load store from a pickle in local workspace

        :return: Store from local or empty store
        """

        filepath = os.path.join(__root_workspace__, f'{cls._kind}.store')
        if Path(filepath).is_file() and os.path.getsize(filepath) > 0:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        else:
            return cls()

    def reset(self) -> None:
        """Calling :meth:`clear` and reset all stats """

        self.clear()
        self.status = self._status_model()
