import os
import glob
import shutil
from pathlib import Path
from itertools import chain
from typing import List, Optional, Tuple

from fastapi import UploadFile
from jina.helper import colored
from jina.logging import JinaLogger

from .base import BaseStore
from ..models import DaemonID
from ..dockerize import Dockerizer
from ..helper import get_workspace_path, random_port_range
from ..excepts import Runtime400Exception
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
    def dockercontext(self) -> str:
        return __rootdir__ if self.build == DaemonBuild.DEVEL else self._workdir

    @property
    def dockerfile(self) -> str:
        return f'{__dockerfiles__}/{self.build.value}.Dockerfile'

    def process_file(self) -> None:
        jinad_file_path = Path(self._workdir) / self.extension
        if jinad_file_path.is_file():
            self.set_args(jinad_file_path)
            return

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

    def _handle_files(self, workspace_id: DaemonID, files: List[UploadFile]):
        workdir = get_workspace_path(workspace_id)
        Path(workdir).mkdir(parents=True, exist_ok=True)
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

    @BaseStore.dump
    def add(self, files: List[UploadFile], **kwargs):
        try:
            workspace_id = DaemonID('jworkspace')
            workdir = get_workspace_path(workspace_id)
            self._handle_files(workspace_id=workspace_id, files=files)
            daemon_file = DaemonFile(workdir=workdir)
            network = Dockerizer.network(workspace_id=workspace_id)
            _min, _max = random_port_range()
            image_id = Dockerizer.build(
                workspace_id=workspace_id, daemon_file=daemon_file
            )
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[workspace_id] = {
                'metadata': {
                    'image_id': image_id,
                    'image_name': workspace_id.tag,
                    'network': network,
                    'ports': {'min': _min, 'max': _max},
                    'workdir': workdir,
                },
                'arguments': {
                    'files': [f.filename for f in files],
                    'jinad': {
                        'build': daemon_file.build,
                        'dockerfile': daemon_file.dockerfile,
                    },
                    'requirements': [],
                },
            }
            self._logger.info(self[workspace_id])
            self._logger.success(f'Workspace {colored(str(workspace_id), "cyan")} is added to stpre')
            return workspace_id

    @BaseStore.dump
    def update(
        self, workspace_id: DaemonID, files: List[UploadFile], **kwargs
    ) -> DaemonID:
        try:
            workdir = get_workspace_path(workspace_id)
            self._handle_files(workspace_id=workspace_id, files=files)
            daemon_file = DaemonFile(workdir=workdir)
            image_id = Dockerizer.build(
                workspace_id=workspace_id, daemon_file=daemon_file
            )
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[workspace_id]['arguments']['files'].extend([f.filename for f in files])
            self[workspace_id]['arguments']['jinad'] = {
                'build': daemon_file.build,
                'dockerfile': daemon_file.dockerfile,
            }
            self[workspace_id]['metadata']['image_id'] = image_id
            return workspace_id

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs):
        if id in self._items:
            Dockerizer.rm_image(id=self[id]['metadata']['image_id'])
            Dockerizer.rm_network(id=self[id]['metadata']['network'])
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
        else:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')
