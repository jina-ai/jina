from typing import List, Optional
from queue import Empty
from threading import Thread

from fastapi import UploadFile
from jina.helper import cached_property, colored
from jina.logging.logger import JinaLogger

from . import __task_queue__, daemon_logger, jinad_args
from .models.id import DaemonID
from .dockerize import Dockerizer
from .models.enums import WorkspaceState
from .stores import workspace_store as store
from .files import DaemonFile, workspace_files
from .excepts import DockerImageException, DockerNetworkException
from .helper import id_cleaner, get_workspace_path, random_port_range
from .models.workspaces import WorkspaceArguments, WorkspaceItem, WorkspaceMetadata


class DaemonWorker(Thread):
    def __init__(
        self, id: 'DaemonID', files: List[UploadFile], name: str, *args, **kwargs
    ) -> None:
        super().__init__(name=f'{self.__class__.__name__}{name}', daemon=True)
        self.id = id
        self.files = files
        self._logger = JinaLogger(
            self.name, workspace_path=self.workdir, **vars(jinad_args)
        )
        self.start()

    @cached_property
    def arguments(self):
        try:
            _args = store[self.id].arguments.copy(deep=True)
            _args.files.extend([f.filename for f in self.files] if self.files else [])
            _args.jinad.update(
                {
                    'build': self.daemon_file.build,
                    'dockerfile': self.daemon_file.dockerfile,
                }
            )
            _args.requirements = self.daemon_file.requirements
        except AttributeError:
            _args = WorkspaceArguments(
                files=[f.filename for f in self.files] if self.files else [],
                jinad={
                    'build': self.daemon_file.build,
                    'dockerfile': self.daemon_file.dockerfile,
                },
                requirements=self.daemon_file.requirements,
            )
        return _args

    @cached_property
    def metadata(self):
        image_id = self.generate_image()
        try:
            _metadata = store[self.id].metadata.copy(deep=True)
            _metadata.image_id = image_id
            _metadata.image_name = self.id.tag
        except AttributeError:
            _metadata = WorkspaceMetadata(
                image_id=image_id,
                image_name=self.id.tag,
                network=id_cleaner(self.network_id),
                workdir=self.workdir,
            )
        return _metadata

    @cached_property
    def workdir(self):
        return get_workspace_path(self.id)

    @cached_property
    def daemon_file(self) -> DaemonFile:
        return DaemonFile(workdir=self.workdir, logger=self._logger)

    @cached_property
    def network_id(self):
        return Dockerizer.network(workspace_id=self.id)

    def generate_image(self):
        return Dockerizer.build(
            workspace_id=self.id, daemon_file=self.daemon_file, logger=self._logger
        )

    @cached_property
    def container_id(self) -> Optional[str]:
        if self.daemon_file.run:
            container, _, _ = Dockerizer.run_custom(
                workspace_id=self.id, daemon_file=self.daemon_file
            )
            return id_cleaner(container.id)
        else:
            return None

    def run(self) -> None:
        try:
            store.update(
                id=self.id,
                value=WorkspaceState.UPDATING
                if store[self.id].arguments
                else WorkspaceState.CREATING,
            )
            workspace_files(workspace_id=self.id, files=self.files, logger=self._logger)
            store.update(
                id=self.id,
                value=WorkspaceItem(
                    state=WorkspaceState.ACTIVE,
                    metadata=self.metadata,
                    arguments=self.arguments,
                ),
            )

            # this needs to be done after the initial update, otherwise run won't find the necessary metadata
            # If a container exists already, kill it before running again
            previous_container = store[self.id].metadata.container_id
            if previous_container:
                self._logger.info(f'Deleting previous container {previous_container}')
                store[self.id].metadata.container_id = None
                del self.container_id
                Dockerizer.rm_container(previous_container)

            # Create a new container if necessary
            store[self.id].metadata.container_id = self.container_id

            self._logger.success(
                f'workspace {colored(str(self.id), "cyan")} is updated'
            )
        except DockerNetworkException as e:
            store.update(id=self.id, value=WorkspaceState.FAILED)
            self._logger.error(f'Error while creating the docker network: {e!r}')
        except DockerImageException as e:
            store.update(id=self.id, value=WorkspaceState.FAILED)
            self._logger.error(f'Error while building the docker image: {e!r}')
        except Exception as e:
            # TODO: how to communicate errors to users? users track it via logs?
            # TODO: Handle cleanup in case of exception
            store.update(id=self.id, value=WorkspaceState.FAILED)
            self._logger.error(f'{e!r}')


class ConsumerThread(Thread):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(daemon=True)
        # TODO: This is used for naming the worker, just appending doesn't make sense
        self._workers_count = 0

    def run(self) -> None:
        while True:
            try:
                workspace_id, files = __task_queue__.get()
                daemon_logger.info(
                    f'starting DaemonWorker{self._workers_count} for workspace {colored(workspace_id, "cyan")}'
                )
                DaemonWorker(
                    id=workspace_id, files=files, name=str(self._workers_count)
                )
                self._workers_count += 1
            except ValueError as e:
                daemon_logger.error(
                    f'got an invalid item in the queue. unable to process! {e!r}'
                )
            except Empty:
                pass
