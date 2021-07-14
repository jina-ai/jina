from http import HTTPStatus
from typing import Dict

from .containers import ContainerStore
from ..excepts import Runtime400Exception
from ..helper import ClientSession, raise_if_not_alive


class PeaStore(ContainerStore):
    """A Store of Peas spawned as Containers by Daemon"""

    _kind = 'pea'

    @raise_if_not_alive
    async def _add(self, uri, **kwargs) -> Dict:
        """Sends `POST` request to `mini-jinad` to create a Pea/Pod.

        :param uri: uri of mini-jinad
        :param kwargs: keyword args
        :raises Runtime400Exception: if creation fails
        :return: response from mini-jinad
        """
        self._logger.debug(f'sending POST request to mini-jinad on {uri}/{self._kind}')
        async with ClientSession() as session:
            async with session.post(
                url=f'{uri}/{self._kind}', json=self.params
            ) as response:
                if response.status != HTTPStatus.CREATED:
                    raise Runtime400Exception(
                        f'{self._kind.title()} creation failed: {response.json()}'
                    )
                return await response.json()

    async def _update(self, uri, **kwargs):
        # TODO
        pass

    @raise_if_not_alive
    async def _delete(self, uri, **kwargs) -> Dict:
        """Sends a `DELETE` request to `mini-jinad` to terminate a Pea/Pod

        :param uri: uri of mini-jinad
        :param kwargs: keyword args
        :raises Runtime400Exception: if deletion fails
        :return: response from mini-jinad
        """
        self._logger.debug(
            f'sending DELETE request to mini-jinad on {uri}/{self._kind}'
        )
        async with ClientSession() as session:
            async with session.delete(url=f'{uri}/{self._kind}') as response:
                if response.status != HTTPStatus.OK:
                    raise Runtime400Exception(
                        f'{self._kind.title()} deletion failed: {response.json()}'
                    )
                return await response.json()
