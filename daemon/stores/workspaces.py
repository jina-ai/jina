from typing import Union
from pathlib import Path
from shutil import rmtree

from jina.helper import colored

from .base import BaseStore
from ..models import DaemonID
from ..dockerize import Dockerizer
from ..models.enums import WorkspaceState

from ..models.workspaces import (
    WorkspaceArguments,
    WorkspaceItem,
    WorkspaceMetadata,
    WorkspaceStoreStatus,
)

from .. import __rootdir__, __dockerfiles__


class WorkspaceStore(BaseStore):

    _kind = 'workspace'
    _status_model = WorkspaceStoreStatus

    @BaseStore.dump
    def add(self, id: DaemonID, value: WorkspaceState, **kwargs):
        if isinstance(value, WorkspaceState):
            self[id] = WorkspaceItem(state=value)
        return id

    @BaseStore.dump
    def update(
        self,
        id: DaemonID,
        value: Union[
            WorkspaceItem, WorkspaceState, WorkspaceArguments, WorkspaceMetadata
        ],
        **kwargs,
    ) -> DaemonID:
        if id not in self:
            raise KeyError(f'workspace {id} not found in store')

        if isinstance(value, WorkspaceItem):
            self[id] = value
        elif isinstance(value, WorkspaceArguments):
            self[id].arguments = value
        elif isinstance(value, WorkspaceMetadata):
            self[id].metadata = value
        elif isinstance(value, WorkspaceState):
            self[id].state = value
        else:
            self._logger.error(f'invalid arguments for workspace: {value}')
        return id

    def rm_files(self, id: DaemonID, logs: bool = False):
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

    def rm_network(self, id: DaemonID):
        try:
            network = self[id].metadata.network
            # TODO: check what containers are using this network
            if id in Dockerizer.networks:
                Dockerizer.rm_network(network)
                assert id not in Dockerizer.networks
                self._logger.success(
                    f'network {colored(network, "cyan")} is successfully removed'
                )
            else:
                self._logger.info(f'no network to delete for id {colored(id, "cyan")}')
            if network:
                self[id].metadata.network = None
        except AttributeError as e:
            self._logger.info(f'there\'s no network to remove {e!r}')
        except AssertionError as e:
            self._logger.error(f'something went wrong while removing the container')
            raise

    def rm_container(self, id: DaemonID):
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
        if everything:
            container = True
            network = True
            files = True

        if id not in self:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')

        # Peas/Pods/Flows need to be deleted before networks, files etc can be deleted
        if everything:
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
