from http import HTTPStatus
from typing import Dict, Optional

import aiohttp
from jina.helper import T

from ..excepts import PartialDaemon400Exception
from ..helper import if_alive, error_msg_from


class AiohttpMixin:
    """Mixin to send POST/PUT/DELETE requests to partial-daemon"""

    @if_alive
    async def POST(
        self: T, *, url: str, params: Optional[Dict] = None, json: Optional[Dict] = None
    ):
        """Sends `POST` request to `partial-daemon` to create a Flow/Pea/Pod.

        :param url: uri of partial-daemon
        :param params: query-params to be sent
        :param json: json payload to be sent
        :raises PartialDaemon400Exception: if POST request fails
        :return: response from partial-daemon
        """
        self._logger.debug(f'sending POST request to partial-daemon on {url}')
        async with aiohttp.request(
            method='POST', url=url, params=params, json=json
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.CREATED:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json

    @if_alive
    async def PUT(
        self: T, *, url: str, params: Optional[Dict] = None, json: Optional[Dict] = None
    ):
        """Sends `PUT` request to `partial-daemon` to update a Flow/Pea/Pod.

        :param url: uri of partial-daemon
        :param params: query-params to be sent
        :param json: json payload to be sent
        :raises PartialDaemon400Exception: if PUT request fails
        :return: response from partial-daemon
        """
        self._logger.debug(f'sending PUT request to partial-daemon on {url}')
        async with aiohttp.request(
            method='PUT', url=url, params=params, json=json
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json

    @if_alive
    async def DELETE(self: T, *, url: str):
        """Sends `DELETE` request to `partial-daemon` to terminate a Flow/Pea/Pod.

        :param url: uri of partial-daemon
        :raises PartialDaemon400Exception: if POST request fails
        :return: response from partial-daemon
        """
        self._logger.debug(f'sending DELETE request to partial-daemon on {url}')
        async with aiohttp.request(method='DELETE', url=url) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json
