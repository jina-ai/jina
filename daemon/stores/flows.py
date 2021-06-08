import requests

from ..models import DaemonID
from .containers import ContainerStore


class FlowStore(ContainerStore):
    _kind = 'flow'

    def _add(self, **kwargs):
        try:
            params = {
                'filename': self.params['uses'],
                'id': self.params['identity']
            }
            if 'port_expose' in kwargs:
                params.update({'port_expose': kwargs['port_expose']})

            print(params)
            r = requests.post(
                url=f'{self.host}/flow',
                params=params
            )
        except requests.exceptions.RequestException as ex:
            self._logger.error(f'{ex!r}')
            raise

    def _update(self):
        try:
            # TODO
            requests.post(url=f'{self.host}/flow')
        except requests.exceptions.RequestException as ex:
            raise

    def _delete(self):
        try:
            requests.delete(url=f'{self.host}/flow')
        except requests.exceptions.RequestException as ex:
            raise

    def update(self, id: DaemonID) -> DaemonID:
        # TODO
        pass
