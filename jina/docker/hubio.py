"""Module for wrapping Jina Hub API calls."""

import argparse
import glob
from typing import Dict

from .checker import *
from .helper import archive_package
from .. import __version__ as jina_version, __resources_path__
from ..flow import Flow
from ..helper import (
    colored,
    get_readable_size,
)
from ..importer import ImportExtensions
from ..logging.logger import JinaLogger
from ..logging.profile import TimeContext


_allowed = {
    'name',  # Human-readable title of the image
    'alias',  # The Docker image name
    'description',  # Human-readable description of the software packaged in the image
    'author',  # Contact details of the people or organization responsible for the image (string)
    'url',  # URL to find more information on the image (string)
    'version',  # The version of the manifest protocol
    'avatar',  # A picture that personalizes and distinguishes your image
    'keywords',  # A list of strings help user to filter and locate your package
}


class HubIO:
    """:class:`HubIO` provides the way to interact with Jina Hub registry.

    You can use it with CLI to package a directory into a Jina Hub and publish it to the world.

    Examples:
        - :command:`jina hub push my_executor/` push the executor package to Jina Hub
        - :command:`jina hub pull jinahub/exec.dummy_mwu_encoder:0.0.6` to download the image
    """

    def __init__(self, args: 'argparse.Namespace'):
        """Create a new HubIO.

        :param args: arguments
        """
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))
        self.args = args
        self._load_docker_client()

    def _load_docker_client(self):
        with ImportExtensions(
            required=False,
            help_text='missing "docker" dependency, available CLIs limited to "jina hub [list, new]"'
            'to enable full CLI, please do pip install "jina[docker]"',
        ):
            import docker
            from docker import APIClient, DockerClient

            self._client: DockerClient = docker.from_env()

            # low-level client
            self._raw_client = APIClient(base_url='unix://var/run/docker.sock')

    def new(self, no_input: bool = False) -> None:
        """
        Create a new executor using cookiecutter template.

        :param no_input: Argument to avoid prompting dialogue (just to be used for testing)
        """
        with ImportExtensions(required=True):
            from cookiecutter.main import cookiecutter
            import click  # part of cookiecutter

        # TODO: refactor the cookiecutter template
        cookiecutter_template = 'https://github.com/jina-ai/cookiecutter-jina-hub.git'

        try:
            cookiecutter(
                template=cookiecutter_template,
                overwrite_if_exists=self.args.overwrite,
                output_dir=self.args.output_dir,
                no_input=no_input,
            )
        except click.exceptions.Abort:
            self.logger.info('nothing is created, bye!')

    def push(self) -> None:
        """Push the executor pacakge to Jina Hub."""

        import requests
        import hashlib
        from pathlib import Path

        is_public = False
        if self.args.public:
            is_public = True

        pkg_path = Path(self.args.path)
        if not pkg_path.exists():
            self.logger.critical(
                f'The given executor package folder "{self.args.path}" does not exist, can not push'
            )
            raise FileNotFoundError(
                f'The given executor package folder "{self.args.path}" does not exist, can not push'
            )

        # validate the executor package

        try:
            # archive the executor package
            with TimeContext(f'archiving executor at {self.args.path}', self.logger):
                md5_hash = hashlib.md5()
                bytesio = archive_package(pkg_path)
                content = bytesio.getvalue()
                md5_hash.update(content)

                md5_digest = md5_hash.hexdigest()

            # upload the archived package
            data = {
                'is_public': is_public,
                'md5sum': md5_digest,
                'jina_version': jina_version,
                'overwrite': self.args.overwrite,
                'secret': self.args.secret,
            }

            # TODO: replace with official jina hub url, e.g., http://hub.jina.ai/
            url = 'http://localhost:3001/upload'
            files = {'file': content}
            # upload the archived executor to Jina Hub
            with TimeContext(f'uploading to {url}', self.logger):
                resp = requests.post(url, files=files, data=data)

            if resp.status_code == 201 and resp.json()['success']:
                # result = {
                #     'work_dir': self.args.path,
                #     'hub_url': resp.json()['data']['image'],
                # }
                # return result
                print(resp.json())
            else:
                self.logger.critical(
                    f'There is some errors while pushing executor "{self.args.path}"'
                )

        except Exception as e:  # IO related errors
            self.logger.error(
                f'Error when trying to push the executor at {self.args.path}: {e!r}'
            )
            raise e

    def pull(self) -> None:
        """Pull docker image."""
        check_registry(self.args.registry, self.args.name, self.args.repository)
        try:
            self._docker_login()
            with TimeContext(f'pulling {self.args.name}', self.logger):
                image = self._client.images.pull(self.args.name)
            if isinstance(image, list):
                image = image[0]
            image_tag = image.tags[0] if image.tags else ''
            self.logger.success(
                f'🎉 pulled {image_tag} ({image.short_id}) uncompressed size: {get_readable_size(image.attrs["Size"])}'
            )
        except Exception as ex:
            self.logger.error(
                f'can not pull image {self.args.name} from {self.args.registry} due to {ex!r}'
            )

    def _check_completeness(self) -> Dict:
        self.args.path = self._alias_to_local_path(self.args.path)
        dockerfile_path = get_exist_path(self.args.path, self.args.file)
        manifest_path = get_exist_path(self.args.path, 'manifest.yml')
        self.config_yaml_path = get_exist_path(self.args.path, 'config.yml')
        readme_path = get_exist_path(self.args.path, 'README.md')
        requirements_path = get_exist_path(self.args.path, 'requirements.txt')

        yaml_glob = set(glob.glob(os.path.join(self.args.path, '*.yml')))
        yaml_glob.difference_update({manifest_path, self.config_yaml_path})

        if not self.config_yaml_path:
            self.config_yaml_path = yaml_glob.pop()

        py_glob = glob.glob(os.path.join(self.args.path, '*.py'))

        test_glob = glob.glob(os.path.join(self.args.path, 'tests/test_*.py'))

        completeness = {
            'Dockerfile': dockerfile_path,
            'manifest.yml': manifest_path,
            'config.yml': self.config_yaml_path,
            'README.md': readme_path,
            'requirements.txt': requirements_path,
            '*.yml': yaml_glob,
            '*.py': py_glob,
            'tests': test_glob,
        }

        self.logger.info(
            f'completeness check\n'
            + '\n'.join(
                f'{colored("✓", "green") if v else colored("✗", "red"):>4} {k:<20} {v}'
                for k, v in completeness.items()
            )
            + '\n'
        )

        if not (completeness['Dockerfile'] and completeness['manifest.yml']):
            self.logger.critical(
                'Dockerfile or manifest.yml is not given, can not build'
            )
            raise FileNotFoundError(
                'Dockerfile or manifest.yml is not given, can not build'
            )

        self.manifest = self._read_manifest(manifest_path)
        self.manifest['jina_version'] = jina_version
        self.executor_name = safe_url_name(
            f'{self.args.repository}/'
            + f'{self.manifest["type"]}.{self.manifest["kind"]}.{self.manifest["name"]}'
        )
        self.tag = self.executor_name + f':{self.manifest["version"]}-{jina_version}'
        return completeness

    def _read_manifest(self, path: str, validate: bool = True) -> Dict:
        with open(
            os.path.join(__resources_path__, 'hub-builder', 'manifest.yml')
        ) as fp:
            tmp = JAML.load(
                fp
            )  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

        with open(path) as fp:
            tmp.update(JAML.load(fp))

        if validate:
            self._validate_manifest(tmp)

        return tmp

    def _validate_manifest(self, manifest: Dict) -> None:
        required = {'name', 'type', 'version'}

        # check the required field in manifest
        for r in required:
            if r not in manifest:
                raise ValueError(f'{r} is missing in the manifest.yaml, it is required')

        # check if all fields are there
        for r in _allowed:
            if r not in manifest:
                self.logger.warning(
                    f'{r} is missing in your manifest.yml, you may want to check it'
                )

        # check name
        check_name(manifest['name'])
        # check_image_type
        check_image_type(manifest['type'])
        # check version number
        check_version(manifest['version'])
        # check version number
        check_license(manifest['license'])
        # check platform
        if not isinstance(manifest['platform'], list):
            manifest['platform'] = list(manifest['platform'])
        check_platform(manifest['platform'])

        # replace all chars in value to safe chars
        for k, v in manifest.items():
            if v and isinstance(v, str):
                manifest[k] = remove_control_characters(v)

        # show manifest key-values
        for k, v in manifest.items():
            self.logger.debug(f'{k}: {v}')

    # alias of "new" in cli
    create = new
    init = new
