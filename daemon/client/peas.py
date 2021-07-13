from typing import Dict, Optional, TYPE_CHECKING, Union

import requests

from .base import BaseClient
from .helper import jinad_alive, daemonize, error_msg_from

if TYPE_CHECKING:
    from ..models import DaemonID


class _PeaClient(BaseClient):

    kind = 'pea'
    endpoint = '/peas'

    @jinad_alive
    def create(
        self, workspace_id: Union[str, 'DaemonID'], payload: Dict
    ) -> Optional[str]:
        """Create a remote Pea / Pod

        :param workspace_id: id of workspace where the Pea would live in
        :param payload: json payload
        :return: the identity of the spawned Pea / Pod
        """

        r = requests.post(
            url=self.store_api,
            params={'workspace_id': daemonize(workspace_id)},
            json=payload,
            timeout=self.timeout,
        )
        response_json = r.json()
        if r.status_code == requests.codes.created:
            self.logger.success(
                f'successfully created {self.kind} in workspace {workspace_id}'
            )
            return response_json
        elif r.status_code == requests.codes.unprocessable:
            self.logger.error(
                f'validation error in the payload: {response_json["detail"][0]["msg"]}'
            )
            return None
        else:
            self.logger.error(
                f'{self.kind} creation failed as: {error_msg_from(response_json)}'
            )
            return None

    @jinad_alive
    def delete(self, identity: Union[str, 'DaemonID'], **kwargs) -> bool:
        """Delete a remote pea/pod

        :param identity: the identity of the Pea/Pod
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """

        r = requests.delete(
            url=f'{self.store_api}/{daemonize(identity)}', timeout=self.timeout
        )
        response_json = r.json()
        if r.status_code != requests.codes.ok:
            self.logger.error(
                f'deletion of {self.kind} {identity} failed: {error_msg_from(response_json)}'
            )
        return r.status_code == requests.codes.ok
