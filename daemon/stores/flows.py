from typing import Dict
from http import HTTPStatus

import aiohttp

from .containers import ContainerStore
from ..excepts import PartialDaemon400Exception
from ..helper import if_alive, error_msg_from


class FlowStore(ContainerStore):
    """A Store of Flows spawned as Containers by Daemon"""

    _kind = 'flow'

    @if_alive
    async def _add(self, uri: str, port_expose: int, params: Dict, **kwargs) -> Dict:
        """Sends `POST` request to `mini-jinad` to create a Flow.

        :param uri: uri of mini-jinad
        :param port_expose: port expose for container flow
        :param params: json payload to be sent
        :param kwargs: keyword args
        :raises PartialDaemon400Exception: if creation fails
        :return: response from mini-jinad
        """
        self._logger.debug(f'sending POST request to mini-jinad on {uri}/{self._kind}')
        async with aiohttp.request(
            method='POST',
            url=f'{uri}/{self._kind}',
            params={'port_expose': str(port_expose)},
            json=params,
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.CREATED:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json

    @if_alive
    async def _delete(self, uri, **kwargs) -> Dict:
        """Sends a `DELETE` request to terminate the Flow & remove the container

        :param uri: uri of mini-jinad
        :param kwargs: keyword args
        :raises PartialDaemon400Exception: if deletion fails
        :return: response from mini-jinad
        """
        self._logger.debug(
            f'sending DELETE request to mini-jinad on {uri}/{self._kind}'
        )
        async with aiohttp.request(
            method='DELETE', url=f'{uri}/{self._kind}'
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                raise PartialDaemon400Exception(error_msg_from(response_json))
            return response_json
