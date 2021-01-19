import shutil
import uuid
from collections.abc import MutableMapping
from datetime import datetime
from typing import Dict, Any, Union

from jina.helper import colored
from jina.logging import JinaLogger
from .. import jinad_args


class BaseStore(MutableMapping):

    def __init__(self):
        self._items = {}  # type: Dict['uuid.UUID', Dict[str, Any]]
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self._init_stats()

    def _init_stats(self):
        """Initialize the stats """
        self._time_created = datetime.now()
        self._time_updated = self._time_created
        self._num_add = 0
        self._num_del = 0

    def add(self, *args, **kwargs) -> 'uuid.UUID':
        """Add a new element to the store. This method needs to be overridden by the subclass"""
        raise NotImplementedError

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key: Union['uuid.UUID', str]):
        if isinstance(key, str):
            key = uuid.UUID(key)
        return self._items[key]

    def __delitem__(self, key: Union['uuid.UUID', str]):
        """ Release a Pea/Pod/Flow object from the store """
        if isinstance(key, str):
            key = uuid.UUID(key)

        if key in self._items:
            v = self._items[key]
            if 'object' in v and hasattr(v['object'], 'close'):
                v['object'].close()
            if v.get('workdir', None):
                shutil.rmtree(v['workdir'])
            self._items.pop(key)
            self._time_updated = datetime.now()
            self._logger.success(f'{colored(str(key), "cyan")} is released from the store.')
            self._num_del += 1
        else:
            raise KeyError(f'{colored(str(key), "cyan")} not found in store.')

    def clear(self) -> None:
        keys = list(self._items.keys())
        for k in keys:
            self.pop(k)

    def reset(self) -> None:
        """Calling :meth:`clear` and reset all stats """
        self.clear()
        self._init_stats()

    def __setitem__(self, key: 'uuid.UUID', value: Dict) -> None:
        self._items[key] = value
        t = datetime.now()
        value.update({'time_created': t})
        self._time_updated = t
        self._logger.success(f'{colored(str(key), "cyan")} is added')
        self._num_add += 1

    @property
    def status(self) -> Dict:
        """Return the status of this store as a dict"""
        return {
            'size': len(self._items),
            'time_created': self._time_created,
            'time_updated': self._time_updated,
            'num_add': self._num_add,
            'num_del': self._num_del,
            'items': self._items
        }
