import requests

from .containers import ContainerStore
from ..excepts import Runtime400Exception


class PeaStore(ContainerStore):
    """A Store of Peas spawned by as Containers by Daemon"""

    _kind = 'pea'

    def _add(self):
        try:
            self._logger.debug(
                f'sending POST request to mini-jinad on {self.host}/{self._kind}'
            )
            r = requests.post(url=f'{self.host}/{self._kind}', json=self.params)
            if r.status_code != requests.codes.created:
                raise Runtime400Exception(
                    f'{self._kind.title()} creation failed: {r.json()}'
                )
            return r.json()
        except requests.exceptions.RequestException as ex:
            self._logger.error(f'{ex!r}')
            raise Runtime400Exception(
                f'{self._kind.title()} deletion failed. request timed out'
            )

    def _update(self):
        # TODO
        pass

    def _delete(self, host, **kwargs):
        """Sends a delete request to terminate the Pea & remove the container

        :param host: host of mini-jinad
        :param kwargs: keyword args
        :raises Runtime400Exception: if deletion fails
        """
        try:
            self._logger.debug(
                f'sending DELETE request to mini-jinad on {host}/{self._kind}'
            )
            r = requests.delete(url=f'{host}/{self._kind}')
            if r.status_code != requests.codes.ok:
                raise Runtime400Exception(
                    f'{self._kind.title()} deletion failed: {r.json()}'
                )
        except requests.exceptions.RequestException as ex:
            raise Runtime400Exception(
                f'{self._kind.title()} deletion failed. request timed out'
            )
