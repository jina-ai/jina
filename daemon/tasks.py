from typing import List
from queue import Empty
from threading import Thread

from fastapi import UploadFile
from jina.helper import cached_property, colored
from jina.logging import JinaLogger

from . import __task_queue__, daemon_logger
from .models.id import DaemonID
from .dockerize import Dockerizer
from .models.enums import WorkspaceState
from .stores import workspace_store as store
from .files import DaemonFile, workspace_files
from .helper import id_cleaner, get_workspace_path, random_port_range
from .models.workspaces import WorkspaceArguments, WorkspaceItem, WorkspaceMetadata


class DaemonWorker(Thread):
    def __init__(self,
                 id: 'DaemonID',
                 files: List[UploadFile],
                 name: str,
                 *args, **kwargs) -> None:
        super().__init__(name=f'{self.__class__.__name__}{name}',
                         daemon=True)
        self.id = id
        self.files = files
        self._logger = JinaLogger(self.name,
                                  workspace_path=self.workdir)
        self.start()

    @cached_property
    def arguments(self):
        try:
            _args = store[self.id].arguments.copy(deep=True)
            _args.files.extend([f.filename for f in self.files] if self.files else [])
            _args.jinad.update({
                'build': self.daemon_file.build,
                'dockerfile': self.daemon_file.dockerfile,
            })
            _args.requirements = self.daemon_file.requirements
        except AttributeError:
            _args = WorkspaceArguments(
                files=[f.filename for f in self.files] if self.files else [],
                jinad={
                    'build': self.daemon_file.build,
                    'dockerfile': self.daemon_file.dockerfile,
                },
                requirements=self.daemon_file.requirements
            )
        return _args

    @cached_property
    def metadata(self):
        try:
            _metadata = store[self.id].metadata.copy(deep=True)
            _metadata.image_id = self.image_id
            _metadata.image_name = self.id.tag
        except AttributeError:
            _min, _max = random_port_range()
            _metadata = WorkspaceMetadata(
                image_id=self.image_id,
                image_name=self.id.tag,
                network=id_cleaner(self.network_id),
                ports={'min': _min, 'max': _max},
                workdir=self.workdir
            )
        return _metadata

    @cached_property
    def workdir(self):
        return get_workspace_path(self.id)

    @cached_property
    def daemon_file(self) -> 'DaemonFile':
        return DaemonFile(workdir=self.workdir,
                          logger=self._logger)

    @cached_property
    def network_id(self):
        return Dockerizer.network(workspace_id=self.id)

    @cached_property
    def image_id(self):
        return Dockerizer.build(workspace_id=self.id,
                                daemon_file=self.daemon_file,
                                logger=self._logger)

    def run(self) -> None:
        try:
            # TODO: Handle diff in case of "update"
            store.update(id=self.id,
                         value=WorkspaceState.UPDATING if store[self.id].arguments else WorkspaceState.CREATING)
            workspace_files(workspace_id=self.id,
                            files=self.files,
                            logger=self._logger)
            store.update(id=self.id,
                         value=WorkspaceItem(state=WorkspaceState.ACTIVE,
                                             metadata=self.metadata,
                                             arguments=self.arguments))
            self._logger.success(
                f'workspace {colored(str(self.id), "cyan")} is updated'
            )
        except Exception as e:
            # TODO: Handle cleanup in case of exception
            store.update(id=self.id,
                         value=WorkspaceState.FAILED)
            self._logger.error(f'{e!r}')


class ConsumerThread(Thread):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(daemon=True)
        self._workers_count = 0

    def run(self) -> None:
        while True:
            try:
                workspace_id, files = __task_queue__.get()
                daemon_logger.info(f'starting DaemonWorker{self._workers_count} for workspace {workspace_id}')
                DaemonWorker(id=workspace_id,
                             files=files,
                             name=str(self._workers_count))
                self._workers_count += 1
            except ValueError as e:
                daemon_logger.error(f'got an invalid item in the queue. unable to process! {e!r}')
            except Empty:
                pass
