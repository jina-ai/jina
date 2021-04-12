import uuid
from pathlib import Path
from typing import Union

from jina.helper import colored
from .base import BaseStore

class WorkunitStore(BaseStore):
    def __init__(self):
        super().__init__()
        from . import workspace_store
        self._workspace_store = workspace_store

    def add(self, *args, **kwargs) -> 'uuid.UUID':
        """Add a new element to the store. This method needs to be overridden by the subclass"""
        raise NotImplementedError

    def delete(
        self,
        id: Union[str, uuid.UUID],
        workspace: bool = False,
        **kwargs,
    ):
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
            del self[id]
            del self._workspace_store[v.get('workspace_id')]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store along  with workspace \
                    {colored(str(v.get("workspace_id")), "cyan")}.'
            )
        else:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')