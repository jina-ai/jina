import time
from typing import Dict, TYPE_CHECKING

import requests

from jina import __default_host__
from jina.helper import colored, random_port

from .base import BaseStore
from ..models import DaemonID
from ..helper import id_cleaner
from ..dockerize import Dockerizer
from ..excepts import Runtime400Exception
from ..models.containers import (
    ContainerArguments,
    ContainerItem,
    ContainerMetadata,
    ContainerStoreStatus,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


class ContainerStore(BaseStore):
    """A Store of Containers spawned by daemon"""

    _kind = 'container'
    _status_model = ContainerStoreStatus

    def _add(self, *args, **kwargs):
        raise NotImplementedError

    def _delete(self, *args, **kwargs):
        raise NotImplementedError

    def _update(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def ready(self) -> bool:
        for _ in range(20):
            try:
                r = requests.get(f'{self.host}/')
                if r.status_code == requests.codes.ok:
                    return True
            except Exception:
                time.sleep(0.2)
                continue
        return False

    @BaseStore.dump
    def add(
        self, id: DaemonID, workspace_id: DaemonID, params: 'BaseModel', ports: Dict, **kwargs
    ):
        try:
            from . import workspace_store
            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            minid_port = random_port()
            self.host = f'http://0.0.0.0:{minid_port}'
            self.params = params.dict(exclude={'log_config'})
            command = f'jinad --port-expose {minid_port} --mode {self._kind}'
            ports.update({f'{minid_port}/tcp': minid_port})

            container, network, ports = Dockerizer.run(
                workspace_id=workspace_id,
                container_id=id,
                command=command,
                ports=ports
            )
            if not self.ready:
                raise Runtime400Exception(f'{id.type} creation failed')
            self._add(**kwargs)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[id] = ContainerItem(
                metadata=ContainerMetadata(
                    container_id=id_cleaner(container.id),
                    container_name=container.name,
                    image_id=id_cleaner(container.image.id),
                    network=network,
                    ports=ports,
                    host=self.host,
                ),
                arguments=ContainerArguments(command=command),
                workspace_id=workspace_id,
            )
            self._logger.success(
                f'{colored(id, "cyan")} is added to workspace {colored(workspace_id, "cyan")}'
            )
            return id

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs):
        if id in self:
            Dockerizer.rm_container(id=self[id].metadata.container_id)
            del self[id]
            self._logger.success(
                f'{colored(id, "cyan")} is released from the store.'
            )
        else:
            raise KeyError(f'{colored(id, "cyan")} not found in store.')
