from http import HTTPStatus
from typing import Dict, Optional, TYPE_CHECKING, Tuple, Union

import aiohttp

from ..models.id import daemonize
from .base import AsyncBaseClient
from .mixin import AsyncToSyncMixin
from ..helper import error_msg_from, if_alive

if TYPE_CHECKING:
    from ..models import DaemonID


class AsyncPeaClient(AsyncBaseClient):
    """Async Client to create/update/delete Peas on remote JinaD"""

    _kind = 'pea'
    _endpoint = '/peas'

    @if_alive
    async def arguments(self) -> Optional[Dict]:
        """Get all arguments accepted by a remote Pea/Pod

        :return: dict arguments of remote JinaD
        """
        async with aiohttp.request(
            method='GET', url=f'{self.store_api}/arguments', timeout=self.timeout
        ) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()

    @if_alive
    async def create(
        self, workspace_id: Union[str, 'DaemonID'], payload: Dict
    ) -> Tuple[bool, str]:
        """Create a remote Pea / Pod

        :param workspace_id: id of workspace where the Pea would live in
        :param payload: json payload
        :return: (True if pea creation succeeded) and (the identity of the spawned Pea/Pod or, error message)
        """

        async with aiohttp.request(
            method='POST',
            url=self.store_api,
            params={'workspace_id': daemonize(workspace_id)},
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
                error_msg = f'validation error in the payload: {response_json["detail"][0]["msg"]}'
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
        """Delete a remote Pea/Pod

        :param id: the identity of the Pea/Pod
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


class PeaClient(AsyncToSyncMixin, AsyncPeaClient):
    """Client to create/update/delete Peas on remote JinaD"""
