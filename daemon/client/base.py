import os
import json
import asyncio
from http import HTTPStatus
from typing import Dict, Optional, Union

import aiohttp

from jina import __resources_path__
from jina.logging.logger import JinaLogger
from jina.importer import ImportExtensions

from ..models.id import DaemonID, daemonize
from ..helper import error_msg_from, if_alive


class BaseClient:
    """
    JinaD baseclient.

    :param host: the host address of ``jinad`` instance
    :param port: the port number of ``jinad`` instance
    :param timeout: stop waiting for a response after a given number of seconds with the timeout parameter.
    """

    _kind = ''
    endpoint = '/'

    def __init__(
        self,
        uri: str,
        logger: JinaLogger,
        timeout: int = None,
    ):
        self._logger = logger
        self.timeout = timeout
        self.http_uri = f'http://{uri}'
        self.store_api = f'{self.http_uri}{self.endpoint}'
        self.logstream_api = f'ws://{uri}/logstream'

    @if_alive
    async def alive(self) -> bool:
        """
        Return True if `jinad` is alive at remote

        :return: True if `jinad` is alive at remote else false
        """
        async with aiohttp.request(method='GET', url=self.http_uri) as response:
            return response.status == HTTPStatus.OK

    @if_alive
    async def status(self) -> Optional[Dict]:
        """
        Get status of remote `jinad`

        :return: dict status of remote jinad
        """
        async with aiohttp.request(
            method='GET', url=f'{self.http_uri}/status'
        ) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()

    @if_alive
    async def get(self, identity: Union[str, DaemonID]) -> Optional[Union[str, Dict]]:
        """Get status of the remote object

        :param id: identity of the Pea/Pod
        :raises: requests.exceptions.RequestException
        :return: json response of the remote Pea / Pod status
        """

        async with aiohttp.request(
            method='GET',
            url=f'{self.store_api}/{daemonize(identity, self._kind)}',
        ) as response:
            response_json = await response.json()
            if response.status == HTTPStatus.UNPROCESSABLE_ENTITY:
                self._logger.error(
                    f'validation error in the request: {error_msg_from(response_json)}'
                )
                return response_json['body']
            elif response.status == HTTPStatus.NOT_FOUND:
                self._logger.error(
                    f'couldn\'t find {identity} in remote {self._kind.title()} store'
                )
                return response_json['detail']
            else:
                self._logger.success(f'Found {self._kind.title()} {identity} in store')
                return response_json

    @if_alive
    async def list(self) -> Dict:
        """
        List all objects in the store

        :return: json response of the remote Pea / Pod status
        """
        async with aiohttp.request(method='GET', url=self.store_api) as response:
            response_json = await response.json()
            self._logger.success(
                f'Found {len(response_json.get("items", []))} {self._kind.title()} in store'
            )
            return response_json['items'] if 'items' in response_json else response_json

    async def create(self, *args, **kwargs) -> Dict:
        """
        Create an object in the store

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def delete(self, identity: DaemonID, *args, **kwargs) -> str:
        """
        Delete an object in the store

        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    async def logstream(self, id: str):
        """Websocket log stream from remote Pea / Pod

        :param id:  the identity of that Pea / Pod
        """
        with ImportExtensions(required=True):
            import websockets

        remote_log_config = os.path.join(__resources_path__, 'logging.remote.yml')
        all_remote_loggers = {}
        try:
            url = f'{self.logstream_api}/{id}'
            async with websockets.connect(url) as websocket:
                async for log_line in websocket:
                    try:
                        ll = json.loads(log_line)
                        name = ll['name']
                        if name not in all_remote_loggers:
                            all_remote_loggers[name] = JinaLogger(
                                context=ll['host'], log_config=remote_log_config
                            )

                        all_remote_loggers[name].info(
                            '{host} {name} {type} {message}'.format_map(ll)
                        )
                    except json.decoder.JSONDecodeError:
                        continue
        except websockets.exceptions.ConnectionClosedOK:
            self._logger.warning(f'log streaming is disconnected')
        except websockets.exceptions.WebSocketException as e:
            self._logger.error(
                f'log streaming is disabled, you won\'t see logs on the remote\n Reason: {e!r}'
            )
        except asyncio.CancelledError:
            self._logger.warning(f'log streaming is cancelled')
        finally:
            for l in all_remote_loggers.values():
                l.close()
