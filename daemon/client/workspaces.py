from pathlib import Path
from contextlib import ExitStack
from typing import Dict, List, Optional, Union, TYPE_CHECKING

import requests

from .base import BaseClient
from .helper import jinad_alive, daemonize, error_msg_from

if TYPE_CHECKING:
    from ..models import DaemonID


class _WorkspaceClient(BaseClient):

    kind = 'workspace'
    endpoint = '/workspaces'

    def _files_from(
        self,
        filepaths: Optional[List[str]],
        dirpaths: Optional[List[str]],
        exitstack: ExitStack,
    ) -> set:
        def file_tuple_from(path):
            return ('files', exitstack.enter_context(open(path, 'rb')))

        files = set()
        if filepaths:
            files.update([file_tuple_from(path) for path in filepaths])
        if dirpaths:
            for dirpath in dirpaths:
                for ext in ['*yml', '*yaml', '*py', '*.jinad', 'requirements.txt']:
                    files.update(
                        [file_tuple_from(path) for path in Path(dirpath).rglob(ext)]
                    )
        return files

    @jinad_alive
    def create(
        self,
        filepaths: Optional[List[str]] = None,
        dirpaths: Optional[List[str]] = None,
        workspace_id: Optional[Union[str, 'DaemonID']] = None,
        *args,
        **kwargs,
    ) -> Optional[str]:
        """Create a remote workspace

        :param filepaths: local filepaths to be uploaded to workspace, defaults to None
        :param dirpaths: local directory paths to be uploaded to workspace, defaults to None
        :param workspace_id: workspace id (if already known), defaults to None
        :return: workspace id
        """

        files = set()

        with ExitStack() as file_stack:
            files = self._files_from(
                filepaths,
                dirpaths,
                file_stack,
            )
            if files:
                self.logger.info(f'uploading {len(files)} file(s): {files}')
            r = requests.post(
                url=self.store_api,
                params={'id': daemonize(workspace_id)} if workspace_id else None,
                files=files if files else None,
                timeout=self.timeout,
            )
            response_json = r.json()
            if r.status_code == requests.codes.created:
                self.logger.success(f'successfully created workspace {workspace_id}')
                return response_json
            else:
                self.logger.error(
                    f'{self.kind} creation failed as: {error_msg_from(response_json)}'
                )
                return None

    @jinad_alive
    def delete(
        self,
        identity: Union[str, 'DaemonID'],
        container: bool = True,
        network: bool = True,
        files: bool = True,
        everything: bool = False,
        **kwargs,
    ) -> bool:
        """
        Delete a remote workspace

        :param identity: the identity of that workspace
        :param container: True if workspace container needs to be removed, defaults to True
        :param network: True if network needs to be removed, defaults to True
        :param files: True if files in the workspace needs to be removed, defaults to True
        :param everything: True if everything needs to be removed, defaults to False
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """
        r = requests.delete(
            url=f'{self.store_api}/{daemonize(identity)}',
            params={
                'container': container,
                'network': network,
                'files': files,
                'everything': everything,
            },
            timeout=self.timeout,
        )
        response_json = r.json()
        if r.status_code != requests.codes.ok:
            self.logger.error(
                f'deletion of {self.kind} {identity} failed: {error_msg_from(response_json)}'
            )
        return r.status_code == requests.codes.ok
