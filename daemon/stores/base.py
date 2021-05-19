import os
import shutil
import pickle
from pathlib import Path
from datetime import datetime
from collections.abc import MutableMapping
from typing import Dict, Any, TYPE_CHECKING, Union, Optional


from jina.helper import colored
from jina.logging import JinaLogger
from ..models import DaemonID
from ..dockerize import Dockerizer
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

    def delete(
        self,
        id: DaemonID,
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
        # if isinstance(id, str):
        #     id = DaemonID(id)

        if id in self._items:
            # v = self._items[id]
            # if 'object' in v and hasattr(v['object'], 'close'):
            #     v['object'].close()
            # if workspace and v.get('workdir', None):
            #     for path in Path(v['workdir']).rglob('[!logging.log]*'):
            #         if path.is_file():
            #             self._logger.debug(f'file to be deleted: {path}')
            #             path.unlink()
            # if everything and v.get('workdir', None):
            #     self._logger.debug(f'directory to be deleted: {v["workdir"]}')
            #     shutil.rmtree(v['workdir'])
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
            self.dump()
        else:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self) -> str:
        return str(self.status)

    def __getitem__(self, key: DaemonID):
        # if key in self.__dict__:
        #     return self.__dict__[key]
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

    def __setstate__(self, state):
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

    def dump(self) -> None:
        # TODO: make this a decorator
        filepath = os.path.join(__root_workspace__, f'{self._kind}.store')
        # Let's keep a backup for no reason?
        if Path(filepath).is_file():
            shutil.copyfile(filepath, f'{filepath}.backup')
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

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
