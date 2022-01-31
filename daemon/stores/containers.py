import os
import sys
import asyncio
from copy import deepcopy
from platform import uname
from http import HTTPStatus
from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING, List, Optional, Union

import aiohttp

from jina import __docker_host__
from jina.helper import colored, random_port
from jina.enums import RemoteWorkspaceState
from daemon.stores.base import BaseStore
from daemon.dockerize import Dockerizer
from daemon.excepts import PartialDaemon400Exception, PartialDaemonConnectionException
from daemon.helper import id_cleaner
from daemon.models import DaemonID
from daemon.models.ports import PortMappings
from daemon.models.containers import (
    ContainerArguments,
    ContainerItem,
    ContainerMetadata,
    ContainerStoreStatus,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


class ContainerStore(BaseStore, ABC):
    """A Store of Containers spawned by daemon"""

    _kind = 'container'
    _status_model = ContainerStoreStatus
    _exposed_ports = set()

    @abstractmethod
    async def add_in_partial(self, uri, envs, *args, **kwargs):
        """Implements jina object creation in `partial-daemon`

        .. #noqa: DAR101"""
        ...

    @abstractmethod
    async def delete_in_partial(self, uri, *args, **kwargs):
        """Implements jina object termination in `partial-daemon`

        .. #noqa: DAR101"""
        ...

    async def ready(self, uri) -> bool:
        """Check if the container with partial-daemon is alive

        :param uri: uri of partial-daemon
        :return: True if partial-daemon is ready"""
        async with aiohttp.ClientSession() as session:
            for _ in range(60):
                try:
                    async with session.get(uri) as response:
                        if response.status == HTTPStatus.OK:
                            self._logger.debug(
                                f'connected to {uri} to create a {self._kind.title()}'
                            )
                            return True
                except aiohttp.ClientConnectionError as e:
                    await asyncio.sleep(0.5)
                    continue
                except Exception as e:
                    self._logger.error(
                        f'error while checking if partial-daemon is ready: {e}'
                    )
        self._logger.error(
            f'couldn\'t reach {self._kind.title()} container at {uri} after 30secs'
        )
        return False

    def _uri(self, port: int) -> str:
        """Returns uri of partial-daemon.

        NOTE: JinaD (running inside a container) needs to access other containers via dockerhost.
        Mac/WSL: this would work as is, as dockerhost is accessible.
        Linux: this would only work if we start jinad passing extra_hosts.

        NOTE: Checks if we actually are in docker (needed for unit tests). If not docker, use localhost.

        :param port: mini jinad port
        :return: uri for partial-daemon
        """

        if (
            sys.platform == 'linux'
            and 'microsoft' not in uname().release
            and not os.path.exists('/.dockerenv')
        ):
            return f'http://localhost:{port}'
        else:
            return f'http://{__docker_host__}:{port}'

    def _entrypoint(self, port: int, workspace_id: DaemonID) -> str:
        """Returns entrypoint for partial-daemon container to be appended to default entrypoint

        NOTE: Important to set `workspace_id` here as this gets set in jina objects in the container

        :param port: partial-daemon port
        :param workspace_id: workspace id
        :return: command for partial-daemon container
        """
        return (
            f'jinad --port {port} --mode {self._kind} --workspace-id {workspace_id.jid}'
        )

    @BaseStore.dump
    async def add(
        self,
        id: DaemonID,
        workspace_id: DaemonID,
        params: 'BaseModel',
        ports: Union[Dict, PortMappings],
        envs: Optional[Dict[str, str]] = {},
        device_requests: Optional[List] = None,
        **kwargs,
    ) -> DaemonID:
        """Add a container to the store

        :param id: id of the container
        :param workspace_id: workspace id where the container lives
        :param params: pydantic model representing the args for the container
        :param ports: ports to be mapped to local
        :param envs: dict of env vars to be passed
        :param device_requests: docker device requests
        :param kwargs: keyword args
        :raises KeyError: if workspace_id doesn't exist in the store or not ACTIVE
        :raises PartialDaemonConnectionException: if jinad cannot connect to partial
        :return: id of the container
        """
        container = None

        try:
            from daemon.stores import workspace_store

            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')
            elif workspace_store[workspace_id].state != RemoteWorkspaceState.ACTIVE:
                raise KeyError(
                    f'{workspace_id} is not ACTIVE yet. Please retry once it becomes ACTIVE'
                )

            dockerports = (
                ports.docker_ports if isinstance(ports, PortMappings) else ports
            )
            with self._lock:
                for port in dockerports.values():
                    self._exposed_ports.add(port)
                partiald_port = self._find_partiald_port()
            dockerports.update({f'{partiald_port}/tcp': partiald_port})
            uri = self._uri(partiald_port)
            entrypoint = self._entrypoint(partiald_port, workspace_id)
            params = params.dict(exclude={'log_config'})

            self._logger.debug(
                'creating container with following arguments \n'
                + '\n'.join(
                    [
                        '{:15s} -> {:15s}'.format('id', id),
                        '{:15s} -> {:15s}'.format('workspace', workspace_id),
                        '{:15s} -> {:15s}'.format('dockerports', str(dockerports)),
                        '{:15s} -> {:15s}'.format('entrypoint', entrypoint),
                    ]
                )
            )

            container, network, dockerports = Dockerizer.run(
                workspace_id=workspace_id,
                container_id=id,
                entrypoint=entrypoint,
                ports=dockerports,
                envs=envs,
                device_requests=device_requests,
            )
            if not await self.ready(uri):
                raise PartialDaemonConnectionException(
                    f'{id.type.title()} creation failed, couldn\'t reach the container at {uri} after 30secs'
                )
            kwargs.update(
                {'ports': ports.dict()} if isinstance(ports, PortMappings) else {}
            )
            object = await self.add_in_partial(uri=uri, params=params, **kwargs)
        except Exception as e:
            self._logger.error(f'{self._kind} creation failed as {e}')
            if container is not None:
                container_logs = Dockerizer.logs(container.id)
                if container_logs and isinstance(
                    e, (PartialDaemon400Exception, PartialDaemonConnectionException)
                ):
                    self._logger.debug(
                        f'error logs from partial daemon: \n {container_logs}'
                    )
                    if e.message and isinstance(e.message, list):
                        e.message += container_logs.split('\n')
                    elif e.message and isinstance(e.message, str):
                        e.message += container_logs
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
                    ports=dockerports,
                    uri=uri,
                ),
                arguments=ContainerArguments(
                    entrypoint=entrypoint,
                    object=object,
                ),
                workspace_id=workspace_id,
            )
            self._logger.success(
                f'{colored(id, "green")} is added to workspace {colored(workspace_id, "green")}'
            )
            workspace_store[workspace_id].metadata.managed_objects.add(id)
            return id

    def _find_partiald_port(self):
        exposed_docker_ports = Dockerizer.exposed_ports()
        partiald_port = random_port()
        port_assignment_runs = 0
        while (
            partiald_port in exposed_docker_ports
            or partiald_port in self._exposed_ports
        ):
            if port_assignment_runs >= 2 ** 16:
                raise OSError('No available ports to new container')
            partiald_port = random_port()
            port_assignment_runs += 1
        self._exposed_ports.add(partiald_port)
        return partiald_port

    @BaseStore.dump
    async def delete(self, id: DaemonID, **kwargs) -> None:
        """Delete a container from the store

        :param id: id of the container
        :param kwargs: keyword args
        :raises KeyError: if id doesn't exist in the store
        """
        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        uri = self[id].metadata.uri
        try:
            await self.delete_in_partial(uri=uri)
        except Exception as e:
            self._logger.error(f'Error while deleting the {self._kind.title()}: \n{e}')
            raise
        else:
            workspace_id = self[id].workspace_id
            del self[id]
            from daemon.stores import workspace_store

            Dockerizer.rm_container(id)
            workspace_store[workspace_id].metadata.managed_objects.remove(id)
            self._logger.success(f'{colored(id, "green")} is released from the store.')

    async def clear(self, **kwargs) -> None:
        """Delete all the objects in the store

        :param kwargs: keyward args
        """

        _status = deepcopy(self.status)
        for k in _status.items.keys():
            await self.delete(id=k, workspace=True, **kwargs)
