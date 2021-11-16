from typing import Dict

from .mixin import AiohttpMixin
from .containers import ContainerStore


class PeaStore(ContainerStore, AiohttpMixin):
    """A Store of Peas spawned as Containers by Daemon"""

    _kind = 'pea'

    async def add_in_partial(self, uri: str, params: Dict, **kwargs) -> Dict:
        """Sends `POST` request to `partial-daemon` to create a Pea/Pod.

        :param uri: uri of partial-daemon
        :param params: json payload to be sent
        :param kwargs: keyword args
        :return: response from mini-jinad
        """
        return await self.POST(
            url=f'{uri}/{self._kind}',
            params=None,
            json=params,
        )

    async def delete_in_partial(self, uri, **kwargs) -> Dict:
        """Sends a `DELETE` request to `partial-daemon` to terminate a Pea/Pod

        :param uri: uri of partial-daemon
        :param kwargs: keyword args
        :return: response from partial-daemon
        """
        return await self.DELETE(url=f'{uri}/{self._kind}')
