from pathlib import Path
from http import HTTPStatus
from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Union, TYPE_CHECKING

import aiohttp

from jina.helper import run_async

from .base import BaseClient
from ..models.id import daemonize
from ..helper import error_msg_from, if_alive

if TYPE_CHECKING:
    from ..models import DaemonID


class AsyncWorkspaceClient(BaseClient):

    _kind = 'workspace'
    endpoint = '/workspaces'

    def _files_from(
        self,
        filepaths: Optional[List[str]],
        dirpaths: Optional[List[str]],
        exitstack: AsyncExitStack,
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

    @if_alive
    async def create(
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

        async with AsyncExitStack() as stack:
            files = self._files_from(
                filepaths,
                dirpaths,
                stack,
            )
            if files:
                self._logger.info(f'uploading {len(files)} file(s): {files}')
            response = await stack.enter_async_context(
                aiohttp.request(
                    method='POST',
                    url=self.store_api,
                    params={'id': daemonize(workspace_id)} if workspace_id else None,
                    data=files if files else None,
                )
            )
            response_json = await response.json()
            if response.status == HTTPStatus.CREATED:
                self._logger.success(f'successfully created workspace {workspace_id}')
                return response_json
            else:
                self._logger.error(
                    f'{self._kind.title()} creation failed as: {error_msg_from(response_json)}'
                )
                return None

    @if_alive
    async def delete(
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
        async with aiohttp.request(
            method='DELETE',
            url=f'{self.store_api}/{daemonize(identity)}',
            params={
                'container': container,
                'network': network,
                'files': files,
                'everything': everything,
            },
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                self._logger.error(
                    f'deletion of {self._kind.title()} {identity} failed: {error_msg_from(response_json)}'
                )
            return response.status == HTTPStatus.OK


class WorkspaceClient(AsyncWorkspaceClient):
    def create(self, *args, **kwargs) -> Dict:
        return run_async(super().create, *args, **kwargs)

    def delete(
        self,
        identity: Union[str, 'DaemonID'],
        container: bool = True,
        network: bool = True,
        files: bool = True,
        everything: bool = False,
        **kwargs,
    ):
        return run_async(
            super().delete,
            identity=identity,
            container=container,
            network=network,
            files=files,
            everything=everything,
            **kwargs,
        )
