from daemon.models.containers import ContainerArguments, ContainerItem, ContainerMetadata
from typing import Union
from pydantic import FilePath

from jina.helper import colored
from .base import BaseStore, Dockerizer
from ..dockerize.helper import id_cleaner
from .. import __root_workspace__
from ..excepts import Runtime400Exception
from ..models import DaemonID


class ContainerStore(BaseStore):
    """A Store of Containers spawned by daemon"""

    _kind = 'container'

    @property
    def command(self) -> str:
        raise NotImplementedError

    def add(self,
            id: DaemonID,
            workspace_id: DaemonID,
            **kwargs):
        try:
            from . import workspace_store
            self._logger.info(workspace_store._items)
            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            _container, _network, _success = Dockerizer.run(workspace_id=workspace_id,
                                                            container_id=id,
                                                            command=self.command)
            if not _success:
                raise Runtime400Exception(f'{id.type} creation failed')

        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[id] = {
                'metadata': {
                    'container_id': _container.id,
                    'container_name': _container.name,
                    'image_id': id_cleaner(_container.image.id),
                    'network': _network,
                    'ports': _container.ports
                },
                'workspace_id': workspace_id,
                'arguments': {
                    'command': self.command
                }
            }
            self.dump()
            self._logger.success(
                f'{colored(str(id), "cyan")} is added to workspace {colored(str(workspace_id), "cyan")}'
            )
            return id

    def delete(self, id: DaemonID, **kwargs):
        if id in self._items:
            Dockerizer.rm_container(id=self[id]['metadata']['container_id'])
            super().delete(id=id)
        else:
            raise KeyError(f'{colored(id, "cyan")} not found in store.')
