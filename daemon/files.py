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
            if f.filename == 'requirements.txt':
                _merge_requirement_file(dest, f)
                continue
            logger.warning(
                f'file {f.filename} already exists in workspace {workspace_id}, will be replaced'
            )
        with open(dest, 'wb+') as fp:
            content = f.file.read()
            fp.write(content)
        logger.info(f'saved uploads to {dest}')


def _merge_requirement_file(dest: str, f: UploadFile) -> None:
    """Merge requirement files

    :param dest: existing requirements file location
    :param f: file obj for the new requirements file
    """
    # Open existing requirements in binary mode
    # UploadFile is also in binary mode
    with open(dest, "rb") as existing_requirements_file:
        old_requirements = _read_requirements_file(existing_requirements_file)
    old_requirements.update(_read_requirements_file(f.file))
    # Store merged requirements
    with open(dest, "w") as req_file:
        req_file.write("\n".join(list(old_requirements.values())))


def _read_requirements_file(f) -> Dict:
    """Read requirement.txt file

    :param f: req file object
    :return: dict representing pip requirements
    """
    requirements = {}
    for line in f.readlines():
        line = line.decode()
        requirements[line.split('=')[0]] = line.replace("\n", "")
    return requirements


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
        self._build = DaemonBuild.default
        self._python = PythonVersion.default
        self._run = ''
        self._ports = []
        self.process_file()

    @property
    def build(self) -> str:
        """Property representing build value

        :return: daemon build in the daemonfile
        """
        return self._build

    @build.setter
    def build(self, build: DaemonBuild):
        """Property setter for build

        :param build: allowed values in DaemonBuild
        """
        try:
            self._build = DaemonBuild(build)
        except ValueError:
            self._logger.warning(
                f'invalid value `{build}` passed for \'build\'. allowed values: {DaemonBuild.values}. '
                f'picking default build: {self._build}'
            )

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
    def run(self) -> str:
        """Property representing run command

        :return: run command in the daemonfile
        """
        return self._run

    @run.setter
    def run(self, run: str):
        """Property setter for run command

        :param run: command passed in .jinad file
        """
        self._run = run

    @property
    def ports(self) -> List[int]:
        """Property representing ports

        :return: ports to be mapped in the daemonfile
        """
        return self._ports

    @ports.setter
    def ports(self, ports: List[int]):
        """Property setter for ports command

        :param ports: ports passed in .jinad file
        """
        self._ports = ports

    @cached_property
    def requirements(self) -> str:
        """pip packages mentioned in requirements.txt

        :return: space separated values
        """
        # TODO: merge this with _read_requirements_file()
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
        """directory for docker context during docker build

        :return: docker context directory"""
        return __rootdir__ if self.build == DaemonBuild.DEVEL else self._workdir

    @cached_property
    def dockerfile(self) -> str:
        """location of dockerfile

        :return: location of dockerfile in local directory
        """
        return f'{__dockerfiles__}/{self.build.value}.Dockerfile'

    @cached_property
    def dockerargs(self) -> Dict:
        """dict of args to be passed during docker build

        :return: dict of args to be passed during docker build
        """
        return (
            {'PY_VERSION': self.python.value, 'PIP_REQUIREMENTS': self.requirements}
            if self.build == DaemonBuild.DEVEL
            else {'PY_VERSION': self.python.name.lower()}
        )

    def process_file(self) -> None:
        """Process .jinad file and set args"""
        # Checks if a file .jinad exists in the workspace
        jinad_file_path = Path(self._workdir) / self.extension
        if jinad_file_path.is_file():
            self.set_args(jinad_file_path)
            return

        # TODO (deepankar): this logic isn't needed, only support .jinad
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

    def set_args(self, file: Path) -> None:
        """read .jinad file & set properties

        :param file: .jinad filepath
        """
        from configparser import ConfigParser, DEFAULTSECT

        config = ConfigParser()
        with open(file) as fp:
            config.read_file(chain([f'[{DEFAULTSECT}]'], fp))
            params = dict(config.items(DEFAULTSECT))
        self.build = params.get('build')
        self.python = params.get('python')
        # remove any leading/trailing spaces and quotes
        stripped_run = params.get('run', '').strip()
        if (
            len(stripped_run) > 1
            and stripped_run[0] == '\"'
            and stripped_run[-1] == '\"'
        ):
            stripped_run = stripped_run.strip('\"')
        self.run = stripped_run
        try:
            ports_string = params.get('ports', '')
            self.ports = list(map(int, filter(None, ports_string.split(','))))
        except ValueError:
            self._logger.warning(f'invalid value `{ports_string}` passed for \'ports\'')
            self.ports = []

    def __repr__(self) -> str:
        return (
            f'DaemonFile(build={self.build}, python={self.python}, run={self.run}, '
            f'context={self.dockercontext}, args={self.dockerargs}), '
            f'ports={self.ports})'
        )
