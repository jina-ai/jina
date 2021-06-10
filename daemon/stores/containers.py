import time
from typing import Dict, TYPE_CHECKING

import requests

from jina import __default_host__
from jina.helper import colored, random_port

from .base import BaseStore
from .. import __dockerhost__
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
        """Implements jina object creation in `mini-jinad`"""
        raise NotImplementedError

    def _delete(self, *args, **kwargs):
        """Implements jina object termination in `mini-jinad`"""
        raise NotImplementedError

    def _update(self, *args, **kwargs):
        """Implements jina object update in `mini-jinad`"""
        raise NotImplementedError

    @property
    def ready(self) -> bool:
        for _ in range(20):
            try:
                r = requests.get(f'{self.host}/')
                if r.status_code == requests.codes.ok:
                    self._logger.success(
                        f'Connected to {self.host} to create a {self._kind}'
                    )
                    return True
            except Exception:
                time.sleep(0.5)
                continue
        self._logger.error(f'couldn\'t reach container at {self.host} after 10secs')
        return False

    @BaseStore.dump
    def add(
        self,
        id: DaemonID,
        workspace_id: DaemonID,
        params: 'BaseModel',
        ports: Dict,
        **kwargs,
    ):
        try:
            from . import workspace_store

            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            self.minid_port = random_port()
            # NOTE: jinad when running inside a container needs to access other containers via dockerhost
            # mac/wsl: this would work as is, as dockerhost is accessible.
            # linux: this would only work if we start jinad passing extra_hosts.
            self.host = f'http://{__dockerhost__}:{self.minid_port}'

            self.params = params.dict(exclude={'log_config'})
            # NOTE: `command` is appended to already existing entrypoint, hence removed the prefix `jinad`
            # NOTE: Important to set `workspace_id` here as this gets set in jina objects in the container
            command = f'--port-expose {self.minid_port} --mode {self._kind} --workspace-id {workspace_id.jid}'
            ports.update({f'{self.minid_port}/tcp': self.minid_port})

            container, network, ports = Dockerizer.run(
                workspace_id=workspace_id, container_id=id, command=command, ports=ports
            )
            if not self.ready:
                raise Runtime400Exception(
                    f'{id.type.title()} creation failed, couldn\'t reach the container at {self.host} after 10secs'
                )
            self._add(**kwargs)
        except Exception as e:
            self._logger.error(f'{e}')
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
                f'{colored(id, "green")} is added to workspace {colored(workspace_id, "green")}'
            )
            return id

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs):
        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')
        Dockerizer.rm_container(id=self[id].metadata.container_id)
        del self[id]
        self._logger.success(f'{colored(id, "green")} is released from the store.')
