from http import HTTPStatus
from typing import Union, TYPE_CHECKING, Dict, Optional

import aiohttp

from ..models.id import daemonize
from ..models.enums import UpdateOperation
from ..helper import if_alive, error_msg_from
from .base import AsyncBaseClient
from .mixin import AsyncToSyncMixin

if TYPE_CHECKING:
    from ..models import DaemonID


class AsyncFlowClient(AsyncBaseClient):
    """Async Client to create/update/delete Flows on remote JinaD"""

    _kind = 'flow'
    _endpoint = '/flows'

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
        self,
        workspace_id: 'DaemonID',
        filename: str,
        envs: Dict[str, str] = {},
        *args,
        **kwargs,
    ) -> str:
        """Start a Flow on remote JinaD

        :param workspace_id: workspace id where flow will be created
        :param filename: name of the flow yaml file in the workspace
        :param envs: dict of env vars to be passed
        :param args: positional args
        :param kwargs: keyword args
        :return: flow id
        """
        envs = (
            [('envs', f'{k}={v}') for k, v in envs.items()]
            if envs and isinstance(envs, Dict)
            else []
        )
        async with aiohttp.request(
            method='POST',
            url=self.store_api,
            params=[('workspace_id', workspace_id), ('filename', filename)] + envs,
            timeout=self.timeout,
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.CREATED:
                error_msg = error_msg_from(response_json)
                self._logger.error(
                    f'{self._kind.title()} creation failed as: {error_msg}'
                )
                return error_msg
            self._logger.success(
                f'Remote Flow created successfully with id {response_json}'
            )
            return response_json

    @if_alive
    async def update(
        self, id: Union[str, 'DaemonID'], pod_name: str, dump_path: str, *args, **kwargs
    ) -> str:
        """Update a Flow on remote JinaD (only rolling_update supported)

        :param id: flow id
        :param pod_name: pod name for rolling update
        :param dump_path: path of dump from other flow
        :param args: positional args
        :param kwargs: keyword args
        :return: flow id
        """
        async with aiohttp.request(
            method='PUT',
            url=f'{self.store_api}/{daemonize(id, self._kind)}',
            params={
                'kind': UpdateOperation.ROLLING_UPDATE.value,
                'pod_name': pod_name,
                'dump_path': dump_path,
            },
            timeout=self.timeout,
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                error_msg = error_msg_from(response_json)
                self._logger.error(
                    f'{self._kind.title()} update failed as: {error_msg}'
                )
                return error_msg
            return response_json

    @if_alive
    async def delete(self, id: Union[str, 'DaemonID'], *args, **kwargs) -> bool:
        """Terminate a Flow on remote JinaD

        :param id: flow id
        :param args: positional args
        :param kwargs: keyword args
        :return: True if deletion is successful
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


class FlowClient(AsyncToSyncMixin, AsyncFlowClient):
    """Client to create/update/delete Flows on remote JinaD"""
