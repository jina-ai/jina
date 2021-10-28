import os
import re
from zipfile import ZipFile, is_zipfile
from itertools import chain
from pathlib import Path
from typing import Dict, List, Union

from fastapi import UploadFile

from jina.logging.logger import JinaLogger
from jina.excepts import DaemonInvalidDockerfile
from . import __rootdir__, __dockerfiles__, jinad_args
from .helper import get_workspace_path
from .models import DaemonID
from .models.enums import DaemonDockerfile, PythonVersion


def store_files_in_workspace(
    workspace_id: DaemonID, files: List[UploadFile], logger: "JinaLogger"
) -> None:
    """Store the uploaded files in local disk

    :param workspace_id: workspace id representing the local directory
    :param files: files uploaded to the workspace endpoint
    :param logger: JinaLogger to use
    """
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
        logger.debug(f'saved uploads to {dest}')

        if is_zipfile(dest):
            logger.debug(f'unzipping {dest}')
            with ZipFile(dest, 'r') as f:
                f.extractall(path=workdir)
            os.remove(dest)


def is_requirements_txt(filename) -> bool:
    """Check if filename is of requirements.txt format

    :param filename: filename
    :return: True if filename is in requirements.txt format
    """
    return True if re.match(r'.*requirements.*\.txt$', filename) else False


class DaemonFile:
    """Object representing .jinad file"""

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
        self._build = DaemonDockerfile.default
        self._dockerfile = os.path.join(
            __dockerfiles__, f'{DaemonDockerfile.default}.Dockerfile'
        )
        self._python = PythonVersion.default
        self._jina = 'master'
        self._run = ''
        self._ports = []
        self.process_file()

    @property
    def dockerfile(self) -> str:
        """Property representing dockerfile value

        :return: daemon dockerfile in the daemonfile
        """
        return self._dockerfile

    @dockerfile.setter
    def dockerfile(self, value: Union[DaemonDockerfile, str]):
        """Property setter for dockerfile

        :param value: allowed values in DaemonDockerfile
        """
        try:
            self._dockerfile = os.path.join(
                __dockerfiles__, f'{DaemonDockerfile(value).value}.Dockerfile'
            )
            self._build = DaemonDockerfile(value)
        except ValueError:
            self._logger.debug(
                f'value passed for `dockerfile` not in default list of values: {DaemonDockerfile.values}.'
            )
            if os.path.isfile(os.path.join(self._workdir, value)):
                self._dockerfile = os.path.join(self._workdir, value)
                self._build = DaemonDockerfile.OTHERS
            else:
                self._logger.critical(
                    f'unable to find dockerfile passed at {value}, cannot proceed with the build'
                )
                raise DaemonInvalidDockerfile()

    @property
    def python(self):
        """Property representing python version

        :return: python version in the daemonfile
        """
        return self._python

    @python.setter
    def python(self, python: PythonVersion):
        """Property setter for python version

        :param python: allowed values in PythonVersion
        """
        try:
            self._python = PythonVersion(python)
        except ValueError:
            self._logger.warning(
                f'invalid value `{python}` passed for \'python\'. allowed values: {PythonVersion.values}. '
                f'picking default version: {self._python}'
            )

    @property
    def jinav(self):
        """Property representing python version

        :return: python version in the daemonfile
        """
        return self._jina

    @jinav.setter
    def jinav(self, jinav: str):
        self._jina = jinav

    @property
    def run(self) -> str:
        """Property representing run command

        :return: run command in the daemonfile
        """
        return self._run

    @run.setter
    def run(self, run: str) -> None:
        """Property setter for run command

        :param run: command passed in .jinad file
        """
        # remove any leading/trailing spaces and quotes
        if len(run) > 1 and run[0] == '\"' and run[-1] == '\"':
            run = run.strip('\"')
            self._run = run

    @property
    def ports(self) -> List[int]:
        """Property representing ports

        :return: ports to be mapped in the daemonfile
        """
        return self._ports

    @ports.setter
    def ports(self, ports: str):
        """Property setter for ports command

        :param ports: ports passed in .jinad file
        """
        try:
            self._ports = list(map(int, filter(None, ports.split(','))))
        except ValueError:
            self._logger.warning(f'invalid value `{ports}` passed for \'ports\'')

    @property
    def requirements(self) -> str:
        """pip packages mentioned in requirements.txt

        :return: space separated values
        """
        requirements = ''
        for filename in os.listdir(self._workdir):
            if is_requirements_txt(filename):
                with open(os.path.join(self._workdir, filename)) as f:
                    requirements += ' '.join(f.read().splitlines())
                requirements += ' '
        if not requirements:
            self._logger.warning(
                'please add a requirements.txt file to manage python dependencies in the workspace'
            )
            return ''
        else:
            return requirements.strip()

    @property
    def dockercontext(self) -> str:
        """directory for docker context during docker build

        :return: docker context directory"""
        return __rootdir__ if self._build == DaemonDockerfile.DEVEL else self._workdir

    @property
    def dockerargs(self) -> Dict:
        """dict of args to be passed during docker build

        .. note::
            For DEVEL, we expect an already built jina image to be available locally.
            We only pass the pip requirements as arguments.
            For DEFAULT (cpu), we pass the python version, jina version used to pull the
            image from docker hub in addition to the requirements.

        :return: dict of args to be passed during docker build
        """
        return (
            {'PIP_REQUIREMENTS': self.requirements}
            if self._build == DaemonDockerfile.DEVEL
            else {
                'PIP_REQUIREMENTS': self.requirements,
                'PY_VERSION': self.python.name.lower(),
                'JINA_VERSION': self.jinav,
            }
        )

    def process_file(self) -> None:
        """Process .jinad file and set args"""
        # Checks if a file .jinad exists in the workspace
        jinad_file_path = Path(self._workdir) / self.extension
        if jinad_file_path.is_file():
            self._logger.debug(f'found .jinad file in path {jinad_file_path}')
            self.set_args(jinad_file_path)
        else:
            self._logger.warning(
                f'please add a .jinad file to manage the docker image in the workspace'
            )

    def set_args(self, file: Path) -> None:
        """read .jinad file & set properties

        :param file: .jinad filepath
        """
        from configparser import ConfigParser, DEFAULTSECT

        config = ConfigParser()
        with open(file) as fp:
            config.read_file(chain([f'[{DEFAULTSECT}]'], fp))
            params = dict(config.items(DEFAULTSECT))
        self.dockerfile = params.get('dockerfile', DaemonDockerfile.default)
        self.python = params.get('python')
        self.run = params.get('run', '').strip()
        self.ports = params.get('ports', '')

    def __repr__(self) -> str:
        return (
            f'DaemonFile(dockerfile={self.dockerfile}, python={self.python}, jina={self.jinav}, '
            f'run={self.run}, context={self.dockercontext}, args={self.dockerargs}), '
            f'ports={self.ports})'
        )
