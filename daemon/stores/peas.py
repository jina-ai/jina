from typing import Dict
from http import HTTPStatus

import aiohttp

from .containers import ContainerStore
from ..excepts import PartialDaemon400Exception
from ..helper import if_alive, error_msg_from


class PeaStore(ContainerStore):
    """A Store of Peas spawned as Containers by Daemon"""

    _kind = 'pea'

    @if_alive
    async def _add(self, uri: str, params: Dict, **kwargs) -> Dict:
        """Sends `POST` request to `mini-jinad` to create a Pea/Pod.

        :param uri: uri of mini-jinad
        :param params: json payload to be sent
        :param kwargs: keyword args
        :raises PartialDaemon400Exception: if creation fails
        :return: response from mini-jinad
        """
        self._logger.debug(f'sending POST request to mini-jinad on {uri}/{self._kind}')
        async with aiohttp.request(
            method='POST', url=f'{uri}/{self._kind}', json=params
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.CREATED:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json

    @if_alive
    async def _delete(self, uri, **kwargs) -> Dict:
        """Sends a `DELETE` request to `mini-jinad` to terminate a Pea/Pod

        :param uri: uri of mini-jinad
        :param kwargs: keyword args
        :raises PartialDaemon400Exception: if deletion fails
        :return: response from mini-jinad
        """
        self._logger.debug(
            f'sending DELETE request to mini-jinad on {uri}/{self._kind}'
        )
        async with aiohttp.request('DELETE', url=f'{uri}/{self._kind}') as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json
