import os
import shutil
import pickle
from pathlib import Path
from datetime import datetime
from collections.abc import MutableMapping
from typing import Callable, Dict, Any, TYPE_CHECKING, Union, Optional

from jina.logging import JinaLogger
from ..models import DaemonID
from .. import jinad_args, __root_workspace__


class BaseStore(MutableMapping):
    """The Base class for Jinad stores"""

    _kind = ''

    def __init__(self):
        self._items = {}  # type: Dict[DaemonID, Dict[str, Any]]
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self._init_stats()

    def _init_stats(self):
        """Initialize the stats """
        self._time_created = datetime.now()
        self._time_updated = self._time_created
        self._num_add = 0
        self._num_del = 0

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

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self) -> str:
        return str(self.status)

    def __getitem__(self, key: DaemonID):
        return self._items[key]

    def __setitem__(self, key: DaemonID, value: Dict) -> None:
        self._items[key] = value
        t = datetime.now()
        value.update({'time_created': t})
        self._time_updated = t
        self._num_add += 1

    def __delitem__(self, key: DaemonID):
        """Release a Pea/Pod/Flow object from the store

        :param key: the key of the object


        .. #noqa: DAR201"""
        self._items.pop(key)
        self._time_updated = datetime.now()
        self._num_del += 1

    def __setstate__(self, state: Dict):
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self._init_stats()
        now = datetime.now()
        self._time_created = state.get('time_created', now)
        self._time_updated = state.get('time_updated', now)
        self._num_add = state.get('num_add', 0)
        self._num_del = state.get('num_del', 0)
        self._items = state.get('items', {})

    def __getstate__(self):
        return self.status

    @classmethod
    def dump(cls, func) -> Callable:
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
    def load(cls) -> Union[Dict, 'BaseStore']:
        filepath = os.path.join(__root_workspace__, f'{cls._kind}.store')
        if Path(filepath).is_file() and os.path.getsize(filepath) > 0:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        else:
            return cls()

    def clear(self) -> None:
        """delete all the objects in the store"""

        keys = list(self._items.keys())
        for k in keys:
            self.delete(id=k, workspace=True)

    def reset(self) -> None:
        """Calling :meth:`clear` and reset all stats """
        self.clear()
        self._init_stats()

    @property
    def status(self) -> Dict:
        """Return the status of this store as a dict


        .. #noqa: DAR201"""
        return {
            'size': len(self._items),
            'time_created': self._time_created,
            'time_updated': self._time_updated,
            'num_add': self._num_add,
            'num_del': self._num_del,
            'items': self._items,
        }
