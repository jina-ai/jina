import os
import json
import asyncio
from http import HTTPStatus
from typing import Dict, Optional, Union

import aiohttp

from jina import __resources_path__
from jina.helper import run_async
from jina.logging.logger import JinaLogger

from .mixin import AsyncToSyncMixin
from ..models.id import DaemonID, daemonize
from ..helper import error_msg_from, if_alive


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
        self.timeout = timeout
        self.http_uri = f'http://{uri}'
        self.store_api = f'{self.http_uri}{self._endpoint}'
        self.logstream_api = f'ws://{uri}/logstream'

    @if_alive
    async def alive(self) -> bool:
        """Check if JinaD is alive

        :return: True if JinaD is alive at remote else false
        """
        async with aiohttp.request(method='GET', url=self.http_uri) as response:
            return response.status == HTTPStatus.OK

    @if_alive
    async def status(self) -> Optional[Dict]:
        """Get status of remote JinaD

        :return: dict status of remote JinaD
        """
        async with aiohttp.request(
            method='GET', url=f'{self.http_uri}/status'
        ) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()

    @if_alive
    async def get(self, id: Union[str, DaemonID]) -> Optional[Union[str, Dict]]:
        """Get status of the remote object

        :param id: identity of the Pea/Pod
        :return: response if the remote Flow/Pea/Pod/Workspace exists
        """

        async with aiohttp.request(
            method='GET',
            url=f'{self.store_api}/{daemonize(id, self._kind)}',
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

        :return: json response of the remote Flow/Pea/Pod/Workspace status
        """
        async with aiohttp.request(method='GET', url=self.store_api) as response:
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

    async def create(self, *args, **kwargs) -> Dict:
        """Create a Workspace/Flow/Pea/Pod on remote.
        Must be implemented by the inherited class.

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def update(self, *args, **kwargs) -> Dict:
        """Update a Workspace/Flow/Pea/Pod on remote.
        Must be implemented by the inherited class.

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def delete(self, id: DaemonID, *args, **kwargs) -> str:
        """Delete a Workspace/Flow/Pea/Pod on remote.
        Must be implemented by the inherited class.

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def logstream(self, id: 'DaemonID', timeout: float = None):
        """Websocket log stream from remote Workspace/Flow/Pea/Pod

        :param id: identity of the Workspace/Flow/Pea/Pod
        :param timeout: timeout in seconds for the logstream
        """
        remote_log_config = os.path.join(__resources_path__, 'logging.remote.yml')
        remote_loggers: Dict[str, 'JinaLogger'] = {}
        try:
            id = daemonize(id)
        except TypeError:
            self._logger.error(f'invalid id {id} passed for logstreaming, exiting..')
            return
        url = f'{self.logstream_api}/{id}'
        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    try:
                        async with session.ws_connect(url) as websocket:
                            async for log_line in websocket:
                                try:
                                    if not log_line:
                                        continue
                                    json_log_line = log_line.json()
                                    name = json_log_line.get('name')
                                    if name not in remote_loggers:
                                        remote_loggers[name] = JinaLogger(
                                            context=json_log_line.get('host'),
                                            log_config=remote_log_config,
                                        )

                                    remote_loggers[name].debug(
                                        '{host} {name} {type} {message}'.format_map(
                                            json_log_line
                                        )
                                    )
                                except json.decoder.JSONDecodeError:
                                    continue
                    except aiohttp.WSServerHandshakeError as e:
                        self._logger.error(
                            f'log streaming failed, you won\'t see logs on the remote\n Reason: {e!r}'
                        )
                        continue
                    except asyncio.CancelledError:
                        self._logger.debug(
                            f'successfully cancelled log streaming task for {id}'
                        )
                        break
        finally:
            for logger in remote_loggers.values():
                logger.close()


class BaseClient(AsyncToSyncMixin, AsyncBaseClient):
    """JinaD baseclient"""
