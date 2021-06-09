import time
from typing import Dict, TYPE_CHECKING

import requests

from jina import __default_host__
from jina.helper import cached_property, colored, random_port

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
                time.sleep(0.5)
                continue
        return False

    @cached_property
    def minid_port(self):
        return random_port()

    @cached_property
    def host(self):
        # TODO: jinad when running inside a container needs to access other containers via dockerhost
        # mac/wsl: this would work as is, as dockerhost is accessible.
        # linux: this would only work if we start jinad passing extra_hosts.
        return f'http://{__dockerhost__}:{self.minid_port}'

    @BaseStore.dump
    def add(
        self, id: DaemonID, workspace_id: DaemonID, params: 'BaseModel', ports: Dict, **kwargs
    ):
        try:
            from . import workspace_store
            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            self.params = params.dict(exclude={'log_config'})
            # NOTE: `command` is appended to already existing entrypoint, hence removed the prefix `jinad`
            # NOTE: Important to set `workspace_id` here as this gets set in jina objects in the container
            command = f'--port-expose {self.minid_port} --mode {self._kind} --workspace-id {workspace_id}'
            ports.update({f'{self.minid_port}/tcp': self.minid_port})

            container, network, ports = Dockerizer.run(
                workspace_id=workspace_id,
                container_id=id,
                command=command,
                ports=ports
            )
            if not self.ready:
                self._logger.error('couldn\'t reach container after 10secs')
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
