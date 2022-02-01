from typing import Dict, Optional

from daemon.stores.mixin import AiohttpMixin
from daemon.stores.containers import ContainerStore


class PodStore(ContainerStore, AiohttpMixin):
    """A Store of Pods spawned as Containers by Daemon"""

    _kind = 'pod'

    async def add_in_partial(
        self, uri: str, params: Dict, envs: Optional[Dict] = {}, **kwargs
    ) -> Dict:
        """Sends `POST` request to `partial-daemon` to create a Pod/Deployment.

        :param uri: uri of partial-daemon
        :param params: json payload to be sent
        :param envs: environment variables to be passed into partial pod
        :param kwargs: keyword args
        :return: response from mini-jinad
        """
        return await self.POST(
            url=f'{uri}/{self._kind}',
            params=None,
            json={self._kind: params, 'envs': envs},
        )

    async def delete_in_partial(self, uri, **kwargs) -> Dict:
        """Sends a `DELETE` request to `partial-daemon` to terminate a Pod/Deployment

        :param uri: uri of partial-daemon
        :param kwargs: keyword args
        :return: response from partial-daemon
        """
        return await self.DELETE(url=f'{uri}/{self._kind}')
