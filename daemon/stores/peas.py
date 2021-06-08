import requests

from .containers import ContainerStore


class PeaStore(ContainerStore):
    _kind = 'pea'

    def _add(self):
        try:
            requests.post(
                url=f'{self.host}/{self._kind}',
                json=self.params
            )
        except requests.exceptions.RequestException as ex:
            raise

    def _update(self):
        pass

    def _delete(self):
        try:
            requests.delete(url=f'{self.host}/{self._kind}')
        except requests.exceptions.RequestException as ex:
            raise
