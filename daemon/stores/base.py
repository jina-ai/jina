import shutil
import uuid
from collections.abc import MutableMapping
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Union

from jina.helper import colored
from jina.logging.logger import JinaLogger
from .. import jinad_args


class BaseStore(MutableMapping):
    """The Base class for Jinad stores"""

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
        """Add a new element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def update(self, *args, **kwargs) -> 'uuid.UUID':
        """Updates the element to the store. This method needs to be overridden by the subclass


        .. #noqa: DAR101"""
        raise NotImplementedError

    def delete(
        self,
        id: Union[str, uuid.UUID],
        workspace: bool = False,
        everything: bool = False,
        **kwargs,
    ):
        """delete an object from the store

        :param id: the id of the object
        :param workspace: whether to delete the workdir of the object
        :param everything: whether to delete everything
        :param kwargs: not used
        """
        if isinstance(id, str):
            id = uuid.UUID(id)

        if id in self._items:
            v = self._items[id]
            if 'object' in v and hasattr(v['object'], 'close'):
                v['object'].close()
            if workspace and v.get('workdir', None):
                for path in Path(v['workdir']).rglob('[!logging.log]*'):
                    if path.is_file():
                        self._logger.debug(f'file to be deleted: {path}')
                        path.unlink()
            if everything and v.get('workdir', None):
                self._logger.debug(f'directory to be deleted: {v["workdir"]}')
                shutil.rmtree(v['workdir'])
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
        else:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key: Union['uuid.UUID', str]):
        if isinstance(key, str):
            key = uuid.UUID(key)
        return self._items[key]

    def __delitem__(self, key: uuid.UUID):
        """Release a Pea/Pod/Flow object from the store

        :param key: the key of the object


        .. #noqa: DAR201"""
        self._items.pop(key)
        self._time_updated = datetime.now()
        self._num_del += 1

    def clear(self) -> None:
        """delete all the objects in the store"""

        keys = list(self._items.keys())
        for k in keys:
            self.delete(id=k, workspace=True)

    def reset(self) -> None:
        """Calling :meth:`clear` and reset all stats """
        self.clear()
        self._init_stats()

    def __setitem__(self, key: 'uuid.UUID', value: Dict) -> None:
        self._items[key] = value
        t = datetime.now()
        value.update({'time_created': t})
        self._time_updated = t
        self._num_add += 1

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
