import os
import glob
from pathlib import Path
from itertools import chain
from typing import Dict, List

from fastapi import UploadFile
from jina.helper import cached_property
from jina.logging.logger import JinaLogger

from .models import DaemonID
from .helper import get_workspace_path
from .excepts import Runtime400Exception
from .models.enums import DaemonBuild, PythonVersion
from . import __rootdir__, __dockerfiles__, jinad_args


def workspace_files(
    workspace_id: DaemonID, files: List[UploadFile], logger: 'JinaLogger'
):
    workdir = get_workspace_path(workspace_id)
    Path(workdir).mkdir(parents=True, exist_ok=True)
    if not files:
        logger.warning(f'couldn\'t find any files to upload!')
        return
    for f in files:
        dest = os.path.join(workdir, f.filename)
        if os.path.isfile(dest):
            logger.warning(
                f'file {f.filename} already exists in workspace {workspace_id}, will be replaced'
            )
        with open(dest, 'wb+') as fp:
            content = f.file.read()
            fp.write(content)
        logger.info(f'saved uploads to {dest}')


class DaemonFile:
    # __slots__ = ['_build', '_python', '_run', '_workdir', '_file', '_logger']
    extension = '.jinad'

    def __init__(self, workdir: str, logger: 'JinaLogger' = None) -> None:
        self._logger = (
            logger
            if logger
            else JinaLogger(self.__class__.__name__, **vars(jinad_args))
        )
        self._workdir = workdir
        self._logger.debug(
            f'analysing {self.extension} files in workdir: {self._workdir}'
        )
        self._build = DaemonBuild.default
        self._python = PythonVersion.default
        self._run = ''
        self._ports = []
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
    def ports(self) -> List[int]:
        return self._ports

    @ports.setter
    def ports(self, ports: List[int]):
        self._ports = ports

    @cached_property
    def requirements(self) -> str:
        _req = f'{self._workdir}/requirements.txt'
        if not Path(_req).is_file():
            self._logger.warning(
                'please add a requirements.txt file to manage python dependencies in the workspace'
            )
            return ''
        with open(_req) as f:
            return ' '.join(f.read().splitlines())

    @cached_property
    def dockercontext(self) -> str:
        return __rootdir__ if self.build == DaemonBuild.DEVEL else self._workdir

    @cached_property
    def dockerfile(self) -> str:
        return f'{__dockerfiles__}/{self.build.value}.Dockerfile'

    @cached_property
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
                f'please add a .jinad file to manage the docker image in the workspace'
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
        try:
            ports_string = params.get('ports', '')
            self.ports = list(map(int, filter(None, ports_string.split(','))))
        except ValueError:
            self._logger.warning(f'invalid value `{ports_string}` passed for \'ports\'')
            self.ports = []

    def __repr__(self) -> str:
        return (
            f'DaemonFile(build={self.build}, python={self.python}, run={self.run}, '
            f'context={self.dockercontext}, args={self.dockerargs})'
        )
