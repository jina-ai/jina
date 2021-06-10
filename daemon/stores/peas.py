import requests

from .containers import ContainerStore
from ..excepts import Runtime400Exception


class PeaStore(ContainerStore):
    _kind = 'pea'

    def _add(self):
        try:
            r = requests.post(url=f'{self.host}/{self._kind}', json=self.params)
            if r.status_code != requests.codes.created:
                raise Runtime400Exception(
                    f'{self._kind.title()} creation failed: {r.json()}'
                )
        except requests.exceptions.RequestException as ex:
            self._logger.error(f'{ex!r}')
            raise Runtime400Exception(
                f'{self._kind.title()} creation failed: {r.json()}'
            )

    def _update(self):
        pass

    def _delete(self):
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
