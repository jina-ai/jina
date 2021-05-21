from jina.helper import colored

from .base import BaseStore
from ..models import DaemonID
from .. import __root_workspace__
from ..dockerize import Dockerizer
from ..dockerize.helper import id_cleaner
from ..excepts import Runtime400Exception


class ContainerStore(BaseStore):
    """A Store of Containers spawned by daemon"""

    _kind = 'container'

    @BaseStore.dump
    def add(self,
            id: DaemonID,
            workspace_id: DaemonID,
            command: str,
            **kwargs):
        try:
            from . import workspace_store
            self._logger.info(workspace_store._items)
            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            _container, _network, _success = Dockerizer.run(workspace_id=workspace_id,
                                                            container_id=id,
                                                            command=command)
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
                    'command': command
                }
            }
            self._logger.success(
                f'{colored(str(id), "cyan")} is added to workspace {colored(str(workspace_id), "cyan")}'
            )
            return id

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs):
        if id in self._items:
            Dockerizer.rm_container(id=self[id]['metadata']['container_id'])
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
        else:
            raise KeyError(f'{colored(id, "cyan")} not found in store.')


class PeaStore(ContainerStore):
    _kind = 'pea'


class PodStore(ContainerStore):
    _kind = 'pod'


class FlowStore(ContainerStore):
    _kind = 'flow'
