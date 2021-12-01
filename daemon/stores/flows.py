from typing import TYPE_CHECKING, Dict, Optional

from jina.helper import colored
from .base import BaseStore
from .mixin import AiohttpMixin
from .containers import ContainerStore

if TYPE_CHECKING:
    from ..models import DaemonID


class FlowStore(ContainerStore, AiohttpMixin):
    """A Store of Flows spawned as Containers by Daemon"""

    _kind = 'flow'

    async def add_in_partial(
        self, uri: str, params: Dict, envs: Optional[Dict] = {}, **kwargs
    ) -> Dict:
        """Sends `POST` request to `partial-daemon` to create a Flow.

        :param uri: uri of partial-daemon
        :param params: Flow params
        :param envs: environment variables to be passed into partial flow
        :param kwargs: keyword args
        :return: response from POST request
        """
        ports = kwargs.get('ports', [])
        return await self.POST(
            url=f'{uri}/{self._kind}',
            params=None,
            json={'flow': params, 'ports': ports, 'envs': envs},
        )

    async def delete_in_partial(self, uri: str, **kwargs) -> Dict:
        """Sends a `DELETE` request to `partial-daemon` to terminate the Flow
        and, remove the container.

        :param uri: uri of partial-daemon
        :param kwargs: keyword args
        :return: response from DELETE request
        """
        return await self.DELETE(url=f'{uri}/{self._kind}')

    @BaseStore.dump
    async def rolling_update(
        self, id: 'DaemonID', pod_name: str, uses_with: Optional[Dict] = None
    ) -> 'DaemonID':
        """rolling_update the Flow inside the container

        :param id: id of the Flow
        :param pod_name: Pod in the Flow to be rolling updated
        :param uses_with: the uses_with arguments to update the executor in pod_name
        :raises KeyError: if id doesn't exist in the store
        :return: id of the Flow
        """

        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        try:
            object = await self.PUT(
                url=f'{self[id].metadata.uri}/{self._kind}/rolling_update',
                params={'pod_name': pod_name},
                json=uses_with,
            )
        except Exception as e:
            self._logger.error(f'Error while sending rolling_update to the Flow: \n{e}')
            raise
        else:
            self[id].arguments.object = object
            self._logger.success(f'{colored(id, "green")} is updated successfully')
            return id

    @BaseStore.dump
    async def scale(self, id: 'DaemonID', pod_name: str, replicas: int) -> 'DaemonID':
        """Scale the Flow inside the container

        :param id: id of the Flow
        :param pod_name: Pod in the Flow to be rolling updated
        :param replicas: The number of replicas to scale to
        :raises KeyError: if id doesn't exist in the store
        :return: id of the Flow
        """

        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        try:
            object = await self.PUT(
                url=f'{self[id].metadata.uri}/{self._kind}/scale',
                params={'pod_name': pod_name, 'replicas': replicas},
                json=None,
            )
        except Exception as e:
            self._logger.error(f'Error while scaling the Flow: \n{e}')
            raise
        else:
            self[id].arguments.object = object
            self._logger.success(f'{colored(id, "green")} is scaled successfully')
            return id
