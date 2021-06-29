from pathlib import Path
from shutil import rmtree
from typing import Union

from jina.enums import RemoteWorkspaceState
from jina.helper import colored
from .base import BaseStore
from ..dockerize import Dockerizer
from ..models import DaemonID
from ..models.workspaces import (
    WorkspaceArguments,
    WorkspaceItem,
    WorkspaceMetadata,
    WorkspaceStoreStatus,
)


class WorkspaceStore(BaseStore):
    """A store of workspaces built by Daemon as docker objects"""

    _kind = 'workspace'
    _status_model = WorkspaceStoreStatus

    @BaseStore.dump
    def add(self, id: DaemonID, value: RemoteWorkspaceState, **kwargs):
        """Add a workspace to the store

        :param id: workspace id
        :param value: state of the workspace
        :param kwargs: keyword args
        :return: workspace id
        """
        if isinstance(value, RemoteWorkspaceState):
            self[id] = WorkspaceItem(state=value)
        return id

    @BaseStore.dump
    def update(
        self,
        id: DaemonID,
        value: Union[
            WorkspaceItem, RemoteWorkspaceState, WorkspaceArguments, WorkspaceMetadata
        ],
        **kwargs,
    ) -> DaemonID:
        """Update the workspace

        :param id: workspace id
        :param value: workspace value to be added
        :param kwargs: keyword args
        :raises KeyError: if id doesn't exist in the store
        :return: workspace id
        """
        if id not in self:
            raise KeyError(f'workspace {id} not found in store')

        if isinstance(value, WorkspaceItem):
            self[id] = value
        elif isinstance(value, WorkspaceArguments):
            self[id].arguments = value
        elif isinstance(value, WorkspaceMetadata):
            self[id].metadata = value
        elif isinstance(value, RemoteWorkspaceState):
            self[id].state = value
        else:
            self._logger.error(f'invalid arguments for workspace: {value}')
        return id

    def rm_files(self, id: DaemonID, logs: bool = False) -> None:
        """Remove files from workspace

        :param id: workspace id
        :param logs: True if log files should be removed, defaults to False
        """
        if self[id].metadata:
            workdir = self[id].metadata.workdir
            if not workdir or not Path(workdir).is_dir():
                self._logger.info(f'there\'s nothing to remove in workdir {workdir}')
                return
            if logs:
                self._logger.info(f'asked to remove complete directory: {workdir}')
                rmtree(workdir)
                self[id].metadata.workdir = ''
            else:
                for path in Path(workdir).rglob('[!logging.log]*'):
                    if path.is_file():
                        self._logger.debug(f'file to be deleted: {path}')
                        path.unlink()

    def rm_network(self, id: DaemonID) -> None:
        """Remove docker network

        :param id: workspace id
        """
        try:
            network = self[id].metadata.network
            # TODO: check what containers are using this network
            status = False
            if id in Dockerizer.networks:
                status = Dockerizer.rm_network(network)
            else:
                self._logger.info(f'no network to delete for id {colored(id, "cyan")}')
            if network and status:
                self[id].metadata.network = None
        except AttributeError as e:
            self._logger.info(f'there\'s no network to remove {e!r}')

    def rm_container(self, id: DaemonID) -> None:
        """Remove docker container

        :param id: workspace id
        """
        try:
            container_id = self[id].metadata.container_id
            if id in Dockerizer.containers:
                Dockerizer.rm_container(container_id)
                assert id not in Dockerizer.containers
                self._logger.success(
                    f'container {colored(container_id, "cyan")} is successfully removed'
                )
            else:
                self._logger.info(
                    f'no container to delete for id {colored(id, "cyan")}'
                )
            if container_id:
                self[id].metadata.container_id = None
        except AttributeError as e:
            self._logger.error(f'there\'s no containers to remove {e!r}')
        except AssertionError as e:
            self._logger.error(f'something went wrong while removing the container')
            raise
        except Exception as e:
            self._logger.error(f'something went wrong while removing the container')
            raise

    @BaseStore.dump
    def delete(
        self,
        id: DaemonID,
        container: bool = True,
        network: bool = True,
        files: bool = True,
        everything: bool = False,
        **kwargs,
    ) -> None:
        """Delete a workspace from the store

        :param id: workspace id
        :param container: True if workspace container needs to be removed, defaults to True
        :param network: True if network needs to be removed, defaults to True
        :param files: True if files in the workspace needs to be removed, defaults to True
        :param everything: True if everything needs to be removed, defaults to False
        :param kwargs: keyword args
        :raises KeyError: if id doesn't exist in the store
        """
        if everything:
            container = True
            network = True
            files = True

        if id not in self:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')

        # Peas/Pods/Flows need to be deleted before networks, files etc can be deleted
        if everything and self[id].metadata:
            from . import get_store_from_id

            ids_to_delete = list(self[id].metadata.managed_objects)
            for managed_object in ids_to_delete:
                get_store_from_id(managed_object).delete(id=managed_object)

        if container:
            self.rm_container(id)
        if network:
            self.rm_network(id)
        if files:
            # TODO: deleting files when not deleting container seems unwise
            self.rm_files(id, logs=everything)

        if everything:
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
