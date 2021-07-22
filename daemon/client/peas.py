from http import HTTPStatus
from typing import Dict, Optional, TYPE_CHECKING, Union

import aiohttp
import requests

from jina.helper import run_async

from .base import BaseClient
from ..models.id import daemonize
from ..helper import error_msg_from, if_alive

if TYPE_CHECKING:
    from ..models import DaemonID


class AsyncPeaClient(BaseClient):

    kind = 'pea'
    endpoint = '/peas'

    @if_alive
    async def create(
        self, workspace_id: Union[str, 'DaemonID'], payload: Dict
    ) -> Optional[str]:
        """Create a remote Pea / Pod

        :param workspace_id: id of workspace where the Pea would live in
        :param payload: json payload
        :return: the identity of the spawned Pea / Pod
        """

        async with aiohttp.request(
            method='POST',
            url=self.store_api,
            params={'workspace_id': daemonize(workspace_id)},
            json=payload,
        ) as response:
            response_json = await response.json()
            if response.status == HTTPStatus.CREATED:
                self._logger.success(
                    f'successfully created {self.kind} in workspace {workspace_id}'
                )
                return response_json
            elif response.status == HTTPStatus.UNPROCESSABLE_ENTITY:
                self._logger.error(
                    f'validation error in the payload: {response_json["detail"][0]["msg"]}'
                )
                return None
            else:
                self._logger.error(
                    f'{self.kind} creation failed as: {error_msg_from(response_json)}'
                )
                return None

    @if_alive
    async def delete(self, identity: Union[str, 'DaemonID'], **kwargs) -> bool:
        """Delete a remote pea/pod

        :param identity: the identity of the Pea/Pod
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """

        async with aiohttp.request(
            method='DELETE', url=f'{self.store_api}/{daemonize(identity)}'
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                self._logger.error(
                    f'deletion of {self.kind} {identity} failed: {error_msg_from(response_json)}'
                )
            return response.status == HTTPStatus.OK


class PeaClient(AsyncPeaClient):
    def create(
        self, workspace_id: Union[str, 'DaemonID'], payload: Dict
    ) -> Optional[str]:
        return run_async(super().create, workspace_id=workspace_id, payload=payload)

    def delete(self, identity: Union[str, 'DaemonID'], **kwargs) -> bool:
        return run_async(super().delete, identity=identity, **kwargs)
