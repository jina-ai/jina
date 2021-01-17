import time
import uuid
from collections.abc import MutableMapping
from typing import Dict, Any

from jina.helper import colored
from jina.logging import JinaLogger
from .. import jinad_args
from ..helper import delete_meta_files_from_upload


class BaseStore(MutableMapping):

    def __init__(self):
        self._items = {}  # type: Dict['uuid.UUID', Dict[str, Any]]
        self.last_update = time.perf_counter()
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))

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
            self.last_update = time.perf_counter()
            self._logger.success(f'{key} is released')
        else:
            raise KeyError(f'{key} not found in store.')

    def __setitem__(self, key: 'uuid.UUID', value: Dict) -> None:
        self._items[key] = value
        t = time.perf_counter()
        value.update({'time_start': t})
        self.last_update = t
        self._logger.success(f'add {value!r} with id {colored(str(key), "cyan")} to the store')
