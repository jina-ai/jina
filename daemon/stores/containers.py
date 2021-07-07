import os
import sys
import time
from platform import uname
from typing import Dict, TYPE_CHECKING

import requests

from jina import __docker_host__
from jina.helper import colored, random_port
from .base import BaseStore
from ..dockerize import Dockerizer
from ..excepts import Runtime400Exception
from ..helper import id_cleaner
from ..models import DaemonID
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
        """Implements jina object creation in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    def _update(self, *args, **kwargs):
        """Implements jina object update in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    def _delete(self, *args, **kwargs):
        """Implements jina object termination in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    @property
    def ready(self) -> bool:
        """Check if the container with mini-jinad is alive

        :return: True if mini-jinad is ready"""
        for _ in range(20):
            try:
                r = requests.get(f'{self.host}/')
                if r.status_code == requests.codes.ok:
                    self._logger.success(
                        f'connected to {self.host} to create a {self._kind}'
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
        """Add a container to the store

        :param id: id of the container
        :param workspace_id: workspace id where the container lives
        :param params: pydantic model representing the args for the container
        :param ports: ports to be mapped to local
        :param kwargs: keyword args
        :raises KeyError: if workspace_id doesn't exist in the store
        :raises Runtime400Exception: if container creation fails
        :return: id of the container
        """
        try:
            from . import workspace_store

            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            self.minid_port = random_port()
            # NOTE: jinad when running inside a container needs to access other containers via dockerhost
            # mac/wsl: this would work as is, as dockerhost is accessible.
            # linux: this would only work if we start jinad passing extra_hosts.
            # check if we actually are in docker, needed for unit tests
            # if not docker, use localhost
            if (
                sys.platform == 'linux'
                and 'microsoft' not in uname().release
                and not os.path.exists('/.dockerenv')
            ):
                self.host = f'http://localhost:{self.minid_port}'
            else:
                self.host = f'http://{__docker_host__}:{self.minid_port}'

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
            object = self._add(**kwargs)
        except Exception as e:
            self._logger.error(f'got an error while creating the {self._kind}: \n{e}')
            if id in Dockerizer.containers:
                self._logger.info(f'removing container {id_cleaner(container.id)}')
                Dockerizer.rm_container(container.id)
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
                arguments=ContainerArguments(
                    command=command,
                    object=object,
                ),
                workspace_id=workspace_id,
            )
            self._logger.success(
                f'{colored(id, "green")} is added to workspace {colored(workspace_id, "green")}'
            )

            del self.host
            workspace_store[workspace_id].metadata.managed_objects.add(id)
            return id

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs) -> None:
        """Delete a container from the store

        :param id: id of the container
        :param kwargs: keyword args
        :raises KeyError: if id doesn't exist in the store
        """
        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        self._delete(host=self[id].metadata.host)
        workspace_id = self[id].workspace_id
        del self[id]
        from . import workspace_store

        Dockerizer.rm_container(id)
        workspace_store[workspace_id].metadata.managed_objects.remove(id)
        self._logger.success(f'{colored(id, "green")} is released from the store.')
