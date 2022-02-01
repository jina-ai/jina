from typing import TYPE_CHECKING, Dict, Optional

from jina.helper import colored
from daemon.stores.base import BaseStore
from daemon.stores.pods import PodStore

if TYPE_CHECKING:
    from daemon.models import DaemonID


class DeploymentStore(PodStore):
    """A Store of Deployments spawned as Containers by Daemon"""

    _kind = 'deployment'

    @BaseStore.dump
    async def rolling_update(
        self, id: 'DaemonID', uses_with: Optional[Dict] = None
    ) -> 'DaemonID':
        """rolling_update the Deployment inside the container

        :param id: id of the Deployment
        :param uses_with: the uses_with arguments to update the executor in deployment_name
        :raises KeyError: if id doesn't exist in the store
        :return: id of the Flow
        """

        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        try:
            object = await self.PUT(
                url=f'{self[id].metadata.uri}/{self._kind}/rolling_update',
                params=None,
                json=uses_with,
            )
        except Exception as e:
            self._logger.error(
                f'Error while sending rolling_update to the Deployment: \n{e}'
            )
            raise
        else:
            self[id].arguments.object = object
            self._logger.success(f'{colored(id, "green")} is updated successfully')
            return id

    @BaseStore.dump
    async def scale(self, id: 'DaemonID', replicas: int) -> 'DaemonID':
        """Scale the Deployment inside the container

        :param id: id of the Deployment
        :param replicas: The number of replicas to scale to
        :raises KeyError: if id doesn't exist in the store
        :return: id of the Flow
        """

        if id not in self:
            raise KeyError(f'{colored(id, "red")} not found in store.')

        try:
            object = await self.PUT(
                url=f'{self[id].metadata.uri}/{self._kind}/scale',
                params={'replicas': replicas},
                json=None,
            )
        except Exception as e:
            self._logger.error(f'Error while scaling the Deployment: \n{e}')
            raise
        else:
            self[id].arguments.object = object
            self._logger.success(f'{colored(id, "green")} is scaled successfully')
            return id
