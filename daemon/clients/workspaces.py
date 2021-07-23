import os
import json
import asyncio
from pathlib import Path
from http import HTTPStatus
from contextlib import AsyncExitStack
from typing import Dict, Iterable, List, Optional, Union, TYPE_CHECKING

import aiohttp
from rich.console import Console

from jina.helper import colored
from jina.jaml.helper import complete_path
from jina.enums import RemoteWorkspaceState

from ..models.id import daemonize
from ..models.workspaces import WorkspaceItem
from ..helper import error_msg_from, if_alive
from .base import BaseClient, AsyncBaseClient

if TYPE_CHECKING:
    from ..models import DaemonID
    from rich.status import Status


class AsyncWorkspaceClient(AsyncBaseClient):
    """Async Client to create/update/delete Workspaces on remote JinaD"""

    _kind = 'workspace'
    _endpoint = '/workspaces'
    _item_model_cls = WorkspaceItem

    def _files_in(
        self,
        paths: Union[str, List[str]],
        exitstack: AsyncExitStack,
        complete: bool = False,
    ) -> 'aiohttp.FormData':
        """Walk through paths & prepare formdata to be uploaded

        :param paths: local file/directory paths
        :param exitstack: exitstack used to enter context
        :param complete: True if files need to searched over call stack, defaults to False
        :return: formdata including file information
        """

        data = aiohttp.FormData()

        def add_field_from(path: Path):
            data.add_field(
                name='files',
                value=exitstack.enter_context(
                    open(complete_path(path) if complete else path, 'rb')
                ),
                filename=path.name,
            )

        if not isinstance(paths, Iterable):
            paths = [paths]

        for path in paths:
            try:
                _path = Path(path)
                if _path.is_file():
                    add_field_from(_path)
                elif _path.is_dir():
                    [add_field_from(p) for p in _path.glob('**/*')]
            except TypeError:
                self._logger.error(f'invalid path {path}')
                continue

        self._logger.info(
            f'uploading {len(data._fields)} file(s): '
            f'{", ".join([os.path.basename(f[-1].name) for f in data._fields])}'
        )
        return data

    @if_alive
    async def create(
        self,
        paths: Optional[List[str]] = None,
        id: Optional[Union[str, 'DaemonID']] = None,
        wait: bool = True,
        logs: bool = True,
        complete: bool = False,
        *args,
        **kwargs,
    ) -> Optional[Union[Dict, bool]]:
        """Create a workspace

        :param paths: local file/directory paths to be uploaded to workspace, defaults to None
        :param id: workspace id (if already known), defaults to None
        :param wait: True if we need to wait for workspace creation, defaults to True
        :param logs: True if we stream logs during workspace creation, defaults to True
        :param complete: True if complete_path is used (used by JinadRuntime), defaults to False
        :param args: additional positional args
        :param kwargs: keyword args
        :return: workspace id
        """

        async with AsyncExitStack() as stack:

            console = Console()
            status = stack.enter_context(
                console.status('Workspace: Getting files...', spinner='earth')
            )
            if paths:
                data = self._files_in(paths=paths, exitstack=stack, complete=complete)
            status.update('Workspace: Sending request...')
            response = await stack.enter_async_context(
                aiohttp.request(
                    method='POST',
                    url=self.store_api,
                    params={'id': daemonize(id)} if id else None,
                    data=data if data else None,
                )
            )
            response_json = await response.json()
            workspace_id = next(iter(response_json))

            if response.status == HTTPStatus.CREATED:
                status.update(f'Workspace: {workspace_id} added...')
                if wait:
                    success = await self.wait(id=workspace_id, status=status, logs=logs)
                    return workspace_id if success else None
                else:
                    return response_json
            else:
                self._logger.error(
                    f'{self._kind.title()} creation failed as: {error_msg_from(response_json)}'
                )
                return None

    async def wait(
        self,
        id: 'DaemonID',
        status: 'Status',
        logs: bool = True,
        sleep: int = 2,
    ) -> bool:
        """Wait until workspace creation completes

        :param id: workspace id
        :param status: rich.console.status object to update
        :param logs: True if logs need to be streamed, defaults to True
        :param sleep: sleep time between each check, defaults to 2
        :return: True if workspace creation succeeds
        """
        logstream = asyncio.create_task(self.logstream(id=id)) if logs else None
        while True:
            try:
                response = await self.get(id=id)
                state = self._item_model_cls(**response).state
                status.update(f'Workspace: {state.value.title()}...')
                if state in [
                    RemoteWorkspaceState.PENDING,
                    RemoteWorkspaceState.CREATING,
                    RemoteWorkspaceState.UPDATING,
                ]:
                    await asyncio.sleep(sleep)
                    continue
                elif state == RemoteWorkspaceState.ACTIVE:
                    self._logger.info(f'{colored(id, "cyan")} created successfully')
                    if logstream:
                        logstream.cancel()
                    return True
                elif state == RemoteWorkspaceState.FAILED:
                    self._logger.critical(
                        f'{colored(id, "red")} creation failed. please check logs'
                    )
                    if logstream:
                        logstream.cancel()
                    return False
            except ValueError as e:
                self._logger.error(f'invalid response from remote: {e!r}')
                if logstream:
                    logstream.cancel()
                return False

    @if_alive
    async def delete(
        self,
        id: Union[str, 'DaemonID'],
        container: bool = True,
        network: bool = True,
        files: bool = True,
        everything: bool = False,
        **kwargs,
    ) -> bool:
        """Delete a remote workspace

        :param id: the identity of that workspace
        :param container: True if workspace container needs to be removed, defaults to True
        :param network: True if network needs to be removed, defaults to True
        :param files: True if files in the workspace needs to be removed, defaults to True
        :param everything: True if everything needs to be removed, defaults to False
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """
        async with aiohttp.request(
            method='DELETE',
            url=f'{self.store_api}/{daemonize(id)}',
            params={
                'container': json.dumps(container),  # aiohttp doesn't suppport bool
                'network': json.dumps(network),
                'files': json.dumps(files),
                'everything': json.dumps(everything),
            },
        ) as response:
            response_json = await response.json()
            if response.status != HTTPStatus.OK:
                self._logger.error(
                    f'deletion of {self._kind.title()} {id} failed: {error_msg_from(response_json)}'
                )
            return response.status == HTTPStatus.OK


class WorkspaceClient(BaseClient, AsyncWorkspaceClient):
    """Client to create/update/delete workspaces on remote JinaD"""
