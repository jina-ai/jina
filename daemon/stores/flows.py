from typing import Dict

import requests

from .containers import ContainerStore
from ..excepts import Runtime400Exception
from ..models import DaemonID
from ..models.enums import UpdateOperation


class FlowStore(ContainerStore):
    """A Store of Flows spawned by as Containers by Daemon"""

    # TODO: lot of duplicate code with peas.py, refactor needed

    _kind = 'flow'

    def _add(self, port_expose: int, **kwargs) -> Dict:
        """Sends `post` request to `mini-jinad` to create a Flow.

        :param port_expose: port expose for container flow
        :param kwargs: keyword args
        :return: response from mini-jinad"""
        try:
            r = requests.post(
                url=f'{self.host}/{self._kind}',
                params={'port_expose': port_expose},
                json=self.params,
            )
            if r.status_code != requests.codes.created:
                raise Runtime400Exception(
                    f'{self._kind.title()} creation failed \n{"".join(r.json()["body"])}'
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
        """Sends `put` request to `mini-jinad` to execute a command on a Flow.

        :param id: flow id
        :param kind: type of update command to execute (only rolling_update for now)
        :param dump_path: the path to which to dump on disk
        :param pod_name: pod to target with the dump request
        :param shards: nr of shards to dump
        :return: response from mini-jinad"""
        try:
            params = {
                'kind': kind,
                'dump_path': dump_path,
                'pod_name': pod_name,
                'shards': shards,
            }
            r = requests.put(
                url=f'{self[id].metadata.host}/{self._kind}', params=params
            )

            if r.status_code != requests.codes.ok:
                raise Runtime400Exception(
                    f'{self._kind.title()} update failed \n{"".join(r.json()["body"])}'
                )
            return r.json()

        except requests.exceptions.RequestException as ex:
            self._logger.error(f'{ex!r}')
            raise Runtime400Exception(f'{self._kind.title()} update failed: {r.json()}')

    def _delete(self, host, **kwargs) -> None:
        """Sends a delete request to terminate the Flow & remove the container

        :param host: host of mini-jinad
        :param kwargs: keyword args
        :raises Runtime400Exception: if deletion fails
        """
        try:
            r = requests.delete(url=f'{host}/{self._kind}')
            if r.status_code != requests.codes.ok:
                raise Runtime400Exception(
                    f'{self._kind.title()} deletion failed \n{"".join(r.json()["body"])}'
                )
        except requests.exceptions.RequestException as ex:
            raise Runtime400Exception(f'{self._kind.title()} deletion failed')
