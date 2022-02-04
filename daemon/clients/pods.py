from http import HTTPStatus
from typing import Dict, Optional, TYPE_CHECKING, Tuple, Union

import aiohttp

from daemon.models.id import daemonize
from daemon.clients.base import AsyncBaseClient
from daemon.clients.mixin import AsyncToSyncMixin
from daemon.helper import error_msg_from, if_alive

if TYPE_CHECKING:
    from daemon.models import DaemonID


class AsyncPodClient(AsyncBaseClient):
    """Async Client to create/update/delete Pods on remote JinaD"""

    _kind = 'pod'
    _endpoint = '/pods'

    @if_alive
    async def arguments(self) -> Optional[Dict]:
        """Get all arguments accepted by a remote Pod/Deployment

        :return: dict arguments of remote JinaD
        """
        async with aiohttp.request(
            method='GET', url=f'{self.store_api}/arguments', timeout=self.timeout
        ) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()

    @if_alive
    async def create(
        self,
        workspace_id: Union[str, 'DaemonID'],
        payload: Dict,
        envs: Dict[str, str] = {},
    ) -> Tuple[bool, str]:
        """Create a remote Pod / Deployment

        :param workspace_id: id of workspace where the Pod would live in
        :param payload: json payload
        :param envs: dict of env vars to be passed
        :return: (True if Pod/Deployment creation succeeded) and (the identity of the spawned Pod/Deployment or, error message)
        """
        envs = (
            [('envs', f'{k}={v}') for k, v in envs.items()]
            if envs and isinstance(envs, Dict)
            else []
        )
        async with aiohttp.request(
            method='POST',
            url=self.store_api,
            params=[('workspace_id', daemonize(workspace_id))] + envs,
            json=payload,
            timeout=self.timeout,
        ) as response:
            response_json = await response.json()
            if response.status == HTTPStatus.CREATED:
                self._logger.success(
                    f'successfully created a {self._kind.title()} {response_json} in workspace {workspace_id}'
                )
                return True, response_json
            elif response.status == HTTPStatus.UNPROCESSABLE_ENTITY:
                field_msg = (
                    f' for field {response_json["detail"][0]["loc"][1]}'
                    if 'loc' in response_json["detail"][0]
                    else ''
                )
                error_msg = f'validation error in the payload: {response_json["detail"][0]["msg"]}{field_msg}'
                self._logger.error(error_msg)
                return False, error_msg
            else:
                error_msg = error_msg_from(response_json)
                self._logger.error(
                    f'{self._kind.title()} creation failed as: {error_msg}'
                )
                return False, error_msg

    @if_alive
    async def delete(self, id: Union[str, 'DaemonID'], **kwargs) -> bool:
        """Delete a remote Pod/Deployment

        :param id: the identity of the Pod/Deployment
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """

        async with aiohttp.request(
            method='DELETE',
            url=f'{self.store_api}/{daemonize(id, self._kind)}',
            timeout=self.timeout,
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                self._logger.error(
                    f'deletion of {self._kind.title()} {id} failed: {error_msg_from(response_json)}'
                )
            return response.status == HTTPStatus.OK


class PodClient(AsyncToSyncMixin, AsyncPodClient):
    """Client to create/update/delete Pods on remote JinaD"""
