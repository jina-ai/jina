import os
import glob
from pathlib import Path
from itertools import chain
from typing import Dict, List, Tuple

from fastapi import UploadFile
from jina.helper import colored
from jina.logging import JinaLogger

from .base import BaseStore
from ..models import DaemonID
from ..dockerize import Dockerizer
from ..helper import get_workspace_path, id_cleaner, random_port_range
from ..excepts import Runtime400Exception
from ..models.workspaces import (
    WorkspaceArguments,
    WorkspaceItem,
    WorkspaceMetadata,
    WorkspaceStoreStatus,
)
from ..models.enums import DaemonBuild, PythonVersion
from .. import __rootdir__, __dockerfiles__, jinad_args


class DaemonFile:
    __slots__ = ['_build', '_python', '_run', '_workdir', '_file', '_logger']
    extension = '.jinad'

    def __init__(self, workdir: str) -> None:
        self._logger = JinaLogger(self.__class__.__name__, **vars(jinad_args))
        self._workdir = workdir
        self._logger.debug(
            f'Analysing {self.extension} files in workdir: {self._workdir}'
        )
        self._build = DaemonBuild.default
        self._python = PythonVersion.default
        self._run = ''
        self.process_file()

    @property
    def build(self):
        return self._build

    @build.setter
    def build(self, build: DaemonBuild):
        try:
            self._build = DaemonBuild(build)
        except ValueError:
            self._logger.warning(
                f'invalid value `{build}` passed for \'build\'. allowed values: {DaemonBuild.values}. '
                f'picking default build: {self._build}'
            )

    @property
    def python(self):
        return self._python

    @python.setter
    def python(self, python: PythonVersion):
        try:
            self._python = PythonVersion(python)
        except ValueError:
            self._logger.warning(
                f'invalid value `{python}` passed for \'python\'. allowed values: {PythonVersion.values}. '
                f'picking default version: {self._python}'
            )

    @property
    def run(self) -> str:
        return self._run

    @run.setter
    def run(self, run: str):
        self._run = run

    @property
    def requirements(self) -> str:
        _req = f'{self._workdir}/requirements.txt'
        if not Path(_req).is_file():
            self._logger.warning(
                'please add a requirements.txt file to manage python dependencies in the workspace'
            )
            return ''
        with open(_req) as f:
            return " ".join(f.read().splitlines())

    @property
    def dockercontext(self) -> str:
        return __rootdir__ if self.build == DaemonBuild.DEVEL else self._workdir

    @property
    def dockerfile(self) -> str:
        return f'{__dockerfiles__}/{self.build.value}.Dockerfile'

    @property
    def dockerargs(self) -> Dict:
        return (
            {'PY_VERSION': self.python.value, 'PIP_REQUIREMENTS': self.requirements}
            if self.build == DaemonBuild.DEVEL
            else {'PY_VERSION': self.python.name.lower()}
        )

    def process_file(self) -> None:
        # Checks if a file .jinad exists in the workspace
        jinad_file_path = Path(self._workdir) / self.extension
        if jinad_file_path.is_file():
            self.set_args(jinad_file_path)
            return

        # Checks alls the .jinad files in the workspace
        _other_jinad_files = glob.glob(f'{Path(self._workdir)}/*{self.extension}')
        if not _other_jinad_files:
            self._logger.warning(
                f'couldn\'t find any `.jinad` file in the workspace. picking defaults..'
            )
        elif len(_other_jinad_files) == 1:
            self.set_args(Path(_other_jinad_files[0]))
        else:
            raise Runtime400Exception(
                f'Multiple .jinad files found in workspace: '
                f'{", ".join([os.path.basename(f) for f in _other_jinad_files])}'
            )

    def set_args(self, file):
        from configparser import ConfigParser, DEFAULTSECT

        config = ConfigParser()
        with open(file) as fp:
            config.read_file(chain([f'[{DEFAULTSECT}]'], fp))
            params = dict(config.items(DEFAULTSECT))
        self.build = params.get('build')
        self.python = params.get('python')
        self.run = params.get('run', '')

    def __repr__(self) -> str:
        return f'DaemonFile(build={self.build}, python={self.python}, run={self.run})'


class WorkspaceStore(BaseStore):

    _kind = 'workspace'
    _status_model = WorkspaceStoreStatus

    def _handle_files(self, workspace_id: DaemonID, files: List[UploadFile]):
        workdir = get_workspace_path(workspace_id)
        Path(workdir).mkdir(parents=True, exist_ok=True)
        if not files:
            self._logger.warning(f'there are no more files to upload!')
            return
        for f in files:
            dest = os.path.join(workdir, f.filename)
            if os.path.isfile(dest):
                self._logger.warning(
                    f'file {f.filename} already exists in workspace {workspace_id}, will be replaced'
                )
            with open(dest, 'wb+') as fp:
                content = f.file.read()
                fp.write(content)
            self._logger.info(f'saved uploads to {dest}')

    def bob_the_builder(self, id: DaemonID, files: List[UploadFile]):
        # Move Bob to the Consumer thread
        workdir = get_workspace_path(id)
        self._handle_files(workspace_id=id, files=files)
        daemon_file = DaemonFile(workdir=workdir)
        network_id = Dockerizer.network(workspace_id=id)
        image_id = Dockerizer.build(workspace_id=id, daemon_file=daemon_file)
        _min, _max = random_port_range()
        return workdir, daemon_file, network_id, image_id, _min, _max

    def _set_id(
        self, id, files, workdir, daemon_file, network_id, image_id, _min, _max
    ):
        # Move this to the Consumer thread
        if id in self:
            if files:
                self[id].arguments.files.extend([f.filename for f in files])
            self[id].arguments.jinad = {
                'build': daemon_file.build,
                'dockerfile': daemon_file.dockerfile,
            }
            self[id].metadata.image_id = image_id
            self[id].arguments.requirements = daemon_file.requirements
            self._logger.success(
                f'Workspace {colored(str(id), "cyan")} is added to store'
            )
        else:
            self[id] = WorkspaceItem(
                metadata=WorkspaceMetadata(
                    image_id=image_id,
                    image_name=id.tag,
                    network=id_cleaner(network_id),
                    ports={'min': _min, 'max': _max},
                    workdir=workdir,
                ),
                arguments=WorkspaceArguments(
                    files=[f.filename for f in files] if files else [],
                    jinad={
                        'build': daemon_file.build,
                        'dockerfile': daemon_file.dockerfile,
                    },
                    requirements=daemon_file.requirements,
                ),
            )
            self._logger.success(f'Workspace {colored(str(id), "cyan")} is updated')
        return id

    @BaseStore.dump
    def add(self, files: List[UploadFile], **kwargs):
        try:
            id = DaemonID('jworkspace')
            (
                workdir,
                daemon_file,
                network_id,
                image_id,
                _min,
                _max,
            ) = self.bob_the_builder(id, files)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            return self._set_id(
                id, files, workdir, daemon_file, network_id, image_id, _min, _max
            )

    @BaseStore.dump
    def update(
        self, id: DaemonID, files: List[UploadFile] = None, **kwargs
    ) -> DaemonID:
        # TODO: Handle POST vs PUT here
        try:
            (
                workdir,
                daemon_file,
                network_id,
                image_id,
                _min,
                _max,
            ) = self.bob_the_builder(id, files)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            return self._set_id(
                id, files, workdir, daemon_file, network_id, image_id, _min, _max
            )

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs):
        if id in self:
            Dockerizer.rm_image(id=self[id].metadata.image_id)
            Dockerizer.rm_network(id=self[id].metadata.network)
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
        else:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')
