import os
import sys
import asyncio
from platform import uname
from http import HTTPStatus
from typing import Dict, TYPE_CHECKING

from jina import __docker_host__
from jina.helper import colored, random_port
from .base import BaseStore
from ..dockerize import Dockerizer
from ..excepts import Runtime400Exception
from ..helper import id_cleaner, ClientSession
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

    async def _add(self, uri, *args, **kwargs):
        """Implements jina object creation in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    async def _update(self, uri, *args, **kwargs):
        """Implements jina object update in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    async def _delete(self, uri, *args, **kwargs):
        """Implements jina object termination in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    async def ready(self, uri) -> bool:
        """Check if the container with mini-jinad is alive

        :return: True if mini-jinad is ready"""
        for _ in range(20):
            try:
                async with ClientSession() as session:
                    async with session.get(uri) as response:
                        if response.status == HTTPStatus.OK:
                            self._logger.success(
                                f'connected to {uri} to create a {self._kind}'
                            )
                            return True
            except Exception:
                await asyncio.sleep(0.5)
                continue
        self._logger.error(f'couldn\'t reach container at {uri} after 10secs')
        return False

    def _uri(self, port: int) -> str:
        """Returns uri of mini-jinad.

        NOTE: JinaD (running inside a container) needs to access other containers via dockerhost.
        Mac/WSL: this would work as is, as dockerhost is accessible.
        Linux: this would only work if we start jinad passing extra_hosts.

        NOTE: Checks if we actually are in docker (needed for unit tests). If not docker, use localhost.

        :param port: mini jinad port
        :return: uri for mini-jinad
        """

        if (
            sys.platform == 'linux'
            and 'microsoft' not in uname().release
            and not os.path.exists('/.dockerenv')
        ):
            return f'http://localhost:{port}'
        else:
            return f'http://{__docker_host__}:{port}'

    def _command(self, port: int, workspace_id: DaemonID) -> str:
        """Returns command for mini-jinad container to be appended to default entrypoint

        NOTE: `command` is appended to already existing entrypoint, hence removed the prefix `jinad`
        NOTE: Important to set `workspace_id` here as this gets set in jina objects in the container

        :param port: [description]
        :param workspace_id: [description]
        :return: [description]
        """
        return f'--port-expose {port} --mode {self._kind} --workspace-id {workspace_id.jid}'

    @BaseStore.dump
    async def add(
        self,
        id: DaemonID,
        workspace_id: DaemonID,
        params: 'BaseModel',
        ports: Dict,
        **kwargs,
    ) -> DaemonID:
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

            minid_port = random_port()
            ports.update({f'{minid_port}/tcp': minid_port})
            uri = self._uri(minid_port)
            command = self._command(minid_port, workspace_id)
            self.params = params.dict(exclude={'log_config'})

            container, network, ports = Dockerizer.run(
                workspace_id=workspace_id, container_id=id, command=command, ports=ports
            )
            if not await self.ready(uri):
                raise Runtime400Exception(
                    f'{id.type.title()} creation failed, couldn\'t reach the container at {uri} after 10secs'
                )
            object = await self._add(uri=uri, **kwargs)
        except Exception as e:
            self._logger.error(f'Error while creating the {self._kind.title()}: \n{e}')
            if id in Dockerizer.containers:
                self._logger.info(f'removing container {id_cleaner(container.id)}')
                # Dockerizer.rm_container(container.id)
            raise
        else:
            self[id] = ContainerItem(
                metadata=ContainerMetadata(
                    container_id=id_cleaner(container.id),
                    container_name=container.name,
                    image_id=id_cleaner(container.image.id),
                    network=network,
                    ports=ports,
                    uri=uri,
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

            workspace_store[workspace_id].metadata.managed_objects.add(id)
            return id

    @BaseStore.dump
    async def update(self, id: DaemonID, **kwargs) -> DaemonID:
        """Update the container in the store

        :param id: id of the container
        :param kwargs: keyword args
        :raises KeyError: [description]
        """
        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        uri = self[id].metadata.uri
        try:
            object = await self._update(uri, **kwargs)
        except Exception as e:
            self._logger.error(f'Error while updating the {self._kind.title()}: \n{e}')
            raise
        else:
            self[id].arguments.object = object
            self._logger.success(f'{colored(id, "green")} is updated successfully')
            return id

    @BaseStore.dump
    async def delete(self, id: DaemonID, **kwargs) -> None:
        """Delete a container from the store

        :param id: id of the container
        :param kwargs: keyword args
        :raises KeyError: if id doesn't exist in the store
        """
        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        await self._delete(uri=self[id].metadata.uri)
        workspace_id = self[id].workspace_id
        del self[id]
        from . import workspace_store

        Dockerizer.rm_container(id)
        workspace_store[workspace_id].metadata.managed_objects.remove(id)
        self._logger.success(f'{colored(id, "green")} is released from the store.')
