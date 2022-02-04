import os
import json
import asyncio
from numbers import Number
from http import HTTPStatus
from typing import Dict, Optional, Union

import aiohttp

from jina import __resources_path__
from jina.logging.logger import JinaLogger

from daemon.clients.mixin import AsyncToSyncMixin
from daemon.models.id import DaemonID, daemonize
from daemon.helper import error_msg_from, if_alive


class AsyncBaseClient:
    """
    JinaD baseclient (Async)

    :param uri: the uri of ``jinad`` instance
    :param logger: jinad logger
    :param timeout: stop waiting for a response after a given number of seconds with the timeout parameter.
    """

    _kind = ''
    _endpoint = '/'

    def __init__(
        self,
        uri: str,
        logger: JinaLogger,
        timeout: int = None,
    ):
        self._logger = logger
        self.timeout = aiohttp.ClientTimeout(
            timeout if isinstance(timeout, Number) else 10 * 60
        )
        self.http_uri = f'http://{uri}'
        self.store_api = f'{self.http_uri}{self._endpoint}'

    @if_alive
    async def alive(self) -> bool:
        """Check if JinaD is alive

        :return: True if JinaD is alive at remote else false
        """
        async with aiohttp.request(
            method='GET', url=self.http_uri, timeout=self.timeout
        ) as response:
            return response.status == HTTPStatus.OK

    @if_alive
    async def status(self) -> Optional[Dict]:
        """Get status of remote JinaD

        :return: dict status of remote JinaD
        """
        async with aiohttp.request(
            method='GET', url=f'{self.http_uri}/status', timeout=self.timeout
        ) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()
            else:
                self._logger.error(
                    f'got response {response.status} while getting status {self._kind}s'
                )

    @if_alive
    async def get(self, id: Union[str, DaemonID]) -> Optional[Union[str, Dict]]:
        """Get status of the remote object

        :param id: identity of the Pod/Deployment
        :return: response if the remote Flow/Pod/Deployment/Workspace exists
        """

        async with aiohttp.request(
            method='GET',
            url=f'{self.store_api}/{daemonize(id, self._kind)}',
            timeout=self.timeout,
        ) as response:
            response_json = await response.json()
            if response.status == HTTPStatus.UNPROCESSABLE_ENTITY:
                self._logger.error(
                    f'validation error in the request: {error_msg_from(response_json)}'
                )
                return response_json['body']
            elif response.status == HTTPStatus.NOT_FOUND:
                self._logger.error(
                    f'couldn\'t find {id} in remote {self._kind.title()} store'
                )
                return response_json['detail']
            else:
                return response_json

    @if_alive
    async def list(self) -> Dict:
        """List all objects in the store

        :return: json response of the remote Flow/Pod/Deployment/Workspace status
        """
        async with aiohttp.request(
            method='GET', url=self.store_api, timeout=self.timeout
        ) as response:
            if response.status == HTTPStatus.OK:
                response_json = await response.json()
                self._logger.success(
                    f'found {len(response_json.get("items", []))} {self._kind.title()}(s) in store'
                )
                return (
                    response_json['items']
                    if 'items' in response_json
                    else response_json
                )
            else:
                self._logger.error(
                    f'got response {response.status} while listing all {self._kind}s'
                )

    @if_alive
    async def clear(self):
        """Send delete request to api

        :return : json response of the remote Flow/Pod/Deployment/Workspace status
        """
        async with aiohttp.request(
            method='DELETE', url=f'{self.store_api}'
        ) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()
            else:
                self._logger.error(
                    f'got response {response.status} while sending delete request {self._kind}s'
                )

    async def create(self, *args, **kwargs) -> Dict:
        """Create a Workspace/Flow/Pod/Deployment on remote.
        Must be implemented by the inherited class.

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def update(self, *args, **kwargs) -> Dict:
        """Update a Workspace/Flow/Pod/Deployment on remote.
        Must be implemented by the inherited class.

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def delete(self, id: DaemonID, *args, **kwargs) -> str:
        """Delete a Workspace/Flow/Pod/Deployment on remote.
        Must be implemented by the inherited class.

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError


class BaseClient(AsyncToSyncMixin, AsyncBaseClient):
    """JinaD baseclient"""
