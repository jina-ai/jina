from typing import Dict, List
import requests

from ..models import DaemonID
from .containers import ContainerStore
from ..excepts import Runtime400Exception


class FlowStore(ContainerStore):
    _kind = 'flow'

    def _add(self, **kwargs) -> Dict:
        """Sends `post` request to `mini-jinad` to create a Flow."""
        try:
            params = {
                'filename': self.params['uses'],
                'id': self.params['identity'],
                'port_expose': self.params['port_expose'],
            }
            r = requests.post(url=f'{self.host}/{self._kind}', params=params)
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

    def _update(self) -> Dict:
        try:
            # TODO
            r = requests.post(url=f'{self.host}/{self._kind}')

        except requests.exceptions.RequestException as ex:
            raise

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

    def update(self, id: DaemonID) -> DaemonID:
        # TODO
        pass
