from typing import Dict, List
import requests

from ..models import DaemonID
from .containers import ContainerStore
from ..excepts import Runtime400Exception
from ..models.enums import UpdateOperation


class FlowStore(ContainerStore):
    _kind = 'flow'

    def _add(self, **kwargs) -> Dict:
        """Sends `post` request to `mini-jinad` to create a Flow."""
        try:
            r = requests.post(url=f'{self.host}/{self._kind}', json=self.params)
            if r.status_code != requests.codes.created:
                raise Runtime400Exception(
                    f'{self._kind.title()} creation failed \n{r.json()}'
                )
            return r.json()
        except requests.exceptions.RequestException as ex:
            self._logger.error(f'{ex!r}')
            raise Runtime400Exception(
                f'{self._kind.title()} creation failed: {r.json()}'
            )

    def update(
        self,
        id: DaemonID,
        kind: UpdateOperation,
        dump_path: str,
        pod_name: str,
        shards: int = None,
    ) -> Dict:
        """Sends `put` request to `mini-jinad` to execute a command on a Flow."""
        try:
            params = {
                'kind': kind,
                'dump_path': dump_path,
                'pod_name': pod_name,
                'shards': shards,
            }
            r = requests.put(url=f'{self.host}/{self._kind}', params=params)

            if r.status_code != requests.codes.ok:
                raise Runtime400Exception(
                    f'{self._kind.title()} update operation {kind} failed \n{r.json()}'
                )
            return r.json()

        except requests.exceptions.RequestException as ex:
            self._logger.error(f'{ex!r}')
            raise Runtime400Exception(
                f'{self._kind.title()} creation failed: {r.json()}'
            )

    def _delete(self):
        """Sends `delete` request to `mini-jinad` to terminate a Flow."""
        try:
            r = requests.delete(url=f'{self.host}/{self._kind}')
            if r.status_code != requests.codes.ok:
                raise Runtime400Exception(
                    f'{self._kind.title()} deletion failed: {r.json()}'
                )
        except requests.exceptions.RequestException as ex:
            raise Runtime400Exception(
                f'{self._kind.title()} deletion failed: {r.json()}'
            )
