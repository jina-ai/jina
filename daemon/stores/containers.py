import os
import sys
import asyncio
from copy import deepcopy
from platform import uname
from http import HTTPStatus
from typing import Dict, TYPE_CHECKING

import aiohttp

from jina import __docker_host__
from jina.helper import colored, random_port
from .base import BaseStore
from ..dockerize import Dockerizer
from ..excepts import (
    PartialDaemon400Exception,
    Runtime400Exception,
    PartialDaemonConnectionException,
)
from ..helper import if_alive, id_cleaner, error_msg_from
from ..models import DaemonID
from ..models.enums import UpdateOperation, IDLiterals
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

    @if_alive
    async def _update(self, uri: str, params: Dict, **kwargs) -> Dict:
        """Sends `PUT` request to `mini-jinad` to execute a command on a Flow.

        :param uri: uri of mini-jinad
        :param params: json payload to be sent
        :param kwargs: keyword args
        :raises PartialDaemon400Exception: if update fails
        :return: response from mini-jinad
        """

        self._logger.debug(f'sending PUT request to mini-jinad on {uri}/{self._kind}')
        async with aiohttp.request(
            method='PUT', url=f'{uri}/{self._kind}', params=params
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json

    async def _delete(self, uri, *args, **kwargs):
        """Implements jina object termination in `mini-jinad`

        .. #noqa: DAR101"""
        raise NotImplementedError

    async def ready(self, uri) -> bool:
        """Check if the container with mini-jinad is alive

        :param uri: uri of mini-jinad
        :return: True if mini-jinad is ready"""
        async with aiohttp.ClientSession() as session:
            for _ in range(20):
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
                        f'error while checking if mini-jinad is ready: {e}'
                    )
        self._logger.error(
            f'couldn\'t reach {self._kind.title()} container at {uri} after 10secs'
        )
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

        :param port: mini jinad port
        :param workspace_id: workspace id
        :return: command for mini-jinad container
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
        :raises PartialDaemonConnectionException: if jinad cannot connect to partial
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
            params = params.dict(exclude={'log_config'})

            self._logger.debug(
                'creating container with following arguments \n'
                + '\n'.join(
                    [
                        '{:15s} -> {:15s}'.format('id', id),
                        '{:15s} -> {:15s}'.format('workspace', workspace_id),
                        '{:15s} -> {:15s}'.format('ports', str(ports)),
                        '{:15s} -> {:15s}'.format('command', command),
                    ]
                )
            )

            container, network, ports = Dockerizer.run(
                workspace_id=workspace_id, container_id=id, command=command, ports=ports
            )
            if not await self.ready(uri):
                raise PartialDaemonConnectionException(
                    f'{id.type.title()} creation failed, couldn\'t reach the container at {uri} after 10secs'
                )
            object = await self._add(uri=uri, params=params, **kwargs)
        except Exception as e:
            self._logger.error(f'{self._kind} creation failed as {e}')
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
    async def update(
        self,
        id: DaemonID,
        kind: UpdateOperation,
        dump_path: str,
        pod_name: str,
        shards: int = None,
        **kwargs,
    ) -> DaemonID:
        """Update the container in the store

        :param id: id of the container
        :param kind: type of update command to execute (only rolling_update for now)
        :param dump_path: the path to which to dump on disk
        :param pod_name: pod to target with the dump request
        :param shards: nr of shards to dump
        :param kwargs: keyword args
        :raises KeyError: if id doesn't exist in the store
        :return: id of the container
        """
        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        if id.jtype == IDLiterals.JFLOW:
            params = {
                'kind': kind.value,
                'dump_path': dump_path,
                'pod_name': pod_name,
            }
            params.update({'shards': shards} if shards else {})
        elif id.jtype == IDLiterals.JPOD:
            params = {'kind': kind.value, 'dump_path': dump_path}
        else:
            self._logger.error(f'update not supported for {id.type} {id}')
            return id

        uri = self[id].metadata.uri
        try:
            object = await self._update(uri, params)
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

        uri = self[id].metadata.uri
        try:
            await self._delete(uri=uri)
        except Exception as e:
            self._logger.error(f'Error while updating the {self._kind.title()}: \n{e}')
            raise
        else:
            workspace_id = self[id].workspace_id
            del self[id]
            from . import workspace_store

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
