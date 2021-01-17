import uuid
from collections.abc import MutableMapping
from datetime import datetime
from typing import Dict, Any

from jina.helper import colored
from jina.logging import JinaLogger
from .. import jinad_args
from ..helper import delete_meta_files_from_upload


class BaseStore(MutableMapping):

    def __init__(self):
        self._items = {}  # type: Dict['uuid.UUID', Dict[str, Any]]
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))

        self._uptime = datetime.now()
        self._last_update = self._uptime
        self._num_add = 0
        self._num_del = 0

    def add(self, *args, **kwargs) -> 'uuid.UUID':
        """Add a new element to the store. This method needs to be overridden by the subclass"""
        raise NotImplementedError

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key: 'uuid.UUID'):
        if isinstance(key, str):
            key = uuid.UUID(key)
        return self._items[key]

    def __delitem__(self, key: 'uuid.UUID'):
        """ Release a Pea/Pod/Flow object from the store """
        if isinstance(key, str):
            key = uuid.UUID(key)

        if key in self._items:
            v = self._items[key]
            if 'object' in v and hasattr(v['object'], 'close'):
                v['object'].close()

            if v.get('files', None):
                for f in v['files']:
                    delete_meta_files_from_upload(current_file=f)

            self._items.pop(key)
            self._last_update = datetime.now()
            self._logger.success(f'{key} is released')
            self._num_del += 1
        else:
            raise KeyError(f'{key} not found in store.')

    def __setitem__(self, key: 'uuid.UUID', value: Dict) -> None:
        self._items[key] = value
        t = datetime.now()
        value.update({'uptime': t})
        self._last_update = t
        self._logger.success(f'add {value!r} with id {colored(str(key), "cyan")} to the store')
        self._num_add += 1

    @property
    def status(self) -> Dict:
        """Return the status of this store as a dict"""
        return {
            'size': len(self._items),
            'uptime': self._uptime,
            'last_update': self._last_update,
            'num_add': self._num_add,
            'num_del': self._num_del,
            'items': self._items
        }
