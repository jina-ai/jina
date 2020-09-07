__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import glob
import tempfile
import urllib.parse
import webbrowser
from typing import Dict

from .checker import *
from .helper import get_default_login
from ..clients.python import ProgressBar
from ..excepts import PeaFailToStart
from ..helper import colored, get_readable_size, get_now_timestamp
from ..logging import get_logger
from ..logging.profile import TimeContext

if False:
    import argparse

_allowed = {'name', 'description', 'author', 'url',
            'documentation', 'version', 'vendor', 'license', 'avatar',
            'platform', 'update', 'keywords'}

_repo_prefix = 'jinahub/'
_label_prefix = 'ai.jina.hub.'


class HubIO:
    """ :class:`HubIO` provides the way to interact with Jina Hub registry.
    You can use it with CLI to package a directory into a Jina Hub image and publish it to the world.

    Examples:
        - :command:`jina hub build my_pod/` build the image
        - :command:`jina hub build my_pod/ --push` build the image and push to the public registry
        - :command:`jina hub pull jinahub/pod.dummy_mwu_encoder:0.0.6` to download the image
    """

    def __init__(self, args: 'argparse.Namespace'):
        self.logger = get_logger(self.__class__.__name__, **vars(args))
        self.args = args
        try:
            import docker
            from docker import APIClient

            self._client = docker.from_env()

            # low-level client
            self._raw_client = APIClient(base_url='unix://var/run/docker.sock')
        except (ImportError, ModuleNotFoundError):
            self.logger.critical('requires "docker" dependency, please install it via "pip install jina[docker]"')
            raise

    def new(self):
        """Create a new executor using cookiecutter template """
        try:
            from cookiecutter.main import cookiecutter
        except (ImportError, ModuleNotFoundError):
            self.logger.critical('requires "cookiecutter" dependency, please install it via "pip install cookiecutter"')
            raise

        cookiecutter(self.args.template, overwrite_if_exists=self.args.overwrite, output_dir=self.args.output_dir)

    def push(self, name: str = None, readme_path: str = None):
        """A wrapper of docker push """
        name = name or self.args.name
        check_registry(self.args.registry, name, _repo_prefix)
        self._check_docker_image(name)
        self.login()
        with ProgressBar(task_name=f'pushing {name}', batch_unit='') as t:
            for line in self._client.images.push(name, stream=True, decode=True):
                t.update(1)
                self.logger.debug(line)
        self.logger.success(f'🎉 {name} is now published!')

        if False and readme_path:
            # unfortunately Docker Hub Personal Access Tokens cannot be used as they are not supported by the API
            _volumes = {os.path.dirname(os.path.abspath(readme_path)): {'bind': '/workspace'}}
            _env = get_default_login()
            _env = {
                'DOCKERHUB_USERNAME': _env['username'],
                'DOCKERHUB_PASSWORD': _env['password'],
                'DOCKERHUB_REPOSITORY': name.split(':')[0],
                'README_FILEPATH': '/workspace/README.md',
            }

            self._client.containers.run('peterevans/dockerhub-description:2.1',
                                        auto_remove=True,
                                        volumes=_volumes,
                                        environment=_env)

        share_link = f'https://api.jina.ai/hub/?jh={urllib.parse.quote_plus(name)}'

        try:
            webbrowser.open(share_link, new=2)
        except:
            pass
        finally:
            self.logger.info(
                f'Check out the usage {colored(share_link, "cyan", attrs=["underline"])} and share it with others!')

    def pull(self):
        """A wrapper of docker pull """
        check_registry(self.args.registry, self.args.name, _repo_prefix)
        self.login()
        with TimeContext(f'pulling {self.args.name}', self.logger):
            image = self._client.images.pull(self.args.name)
        if isinstance(image, list):
            image = image[0]
        image_tag = image.tags[0] if image.tags else ""
        self.logger.success(
            f'🎉 pulled {image_tag} ({image.short_id}) uncompressed size: {get_readable_size(image.attrs["Size"])}')

    def _check_docker_image(self, name: str):
        # check local image
        image = self._client.images.get(name)
        for r in _allowed:
            if f'{_label_prefix}{r}' not in image.labels.keys():
                self.logger.warning(f'{r} is missing in your docker image labels, you may want to check it')
        try:
            if name != safe_url_name(
                    f'{_repo_prefix}' + '{type}.{kind}.{name}:{version}'.format(
                        **{k.replace(_label_prefix, ''): v for k, v in image.labels.items()})):
                raise ValueError(f'image {name} does not match with label info in the image')
        except KeyError:
            self.logger.error('missing key in the label of the image')
            raise

        self.logger.info(f'✅ {name} is a valid Jina Hub image, ready to publish')

    def login(self):
        """A wrapper of docker login """
        try:
            password = self.args.password  # or (self.args.password_stdin and self.args.password_stdin.read())
        except ValueError:
            password = ''

        if self.args.username and password:
            self._client.login(username=self.args.username, password=password,
                               registry=self.args.registry)
        else:
            # use default login
            self._client.login(**get_default_login(), registry=self.args.registry)

    def build(self) -> Dict:
        """A wrapper of docker build """
        if self.args.dry_run:
            result = self.dry_run()
        else:
            is_build_success, is_push_success = True, False
            _logs = []
            _excepts = []

            with TimeContext(f'building {colored(self.args.path, "green")}', self.logger) as tc:
                try:
                    self._check_completeness()

                    streamer = self._raw_client.build(
                        decode=True,
                        path=self.args.path,
                        tag=self.canonical_name,
                        pull=self.args.pull,
                        dockerfile=self.dockerfile_path_revised,
                        rm=True
                    )

                    for chunk in streamer:
                        if 'stream' in chunk:
                            for line in chunk['stream'].splitlines():
                                if is_error_message(line):
                                    self.logger.critical(line)
                                    _excepts.append(line)
                                elif 'warning' in line.lower():
                                    self.logger.warning(line)
                                else:
                                    self.logger.info(line)
                                _logs.append(line)
                except Exception as ex:
                    # if pytest fails it should end up here as well
                    is_build_success = False
                    _excepts.append(str(ex))

            if is_build_success:
                # compile it again, but this time don't show the log
                image, log = self._client.images.build(path=self.args.path,
                                                       tag=self.canonical_name,
                                                       pull=self.args.pull,
                                                       dockerfile=self.dockerfile_path_revised,
                                                       rm=True)

                # success

                _details = {
                    'inspect': self._raw_client.inspect_image(image.tags[0]),
                    'tag': image.tags[0],
                    'hash': image.short_id,
                    'size': get_readable_size(image.attrs['Size']),
                }

                self.logger.success(
                    '🎉 built {tag} ({hash}) uncompressed size: {size}'.format_map(_details))

            else:
                self.logger.error(f'can not build the image, please double check the log')
                _details = {}

            if is_build_success:
                if self.args.test_uses:
                    try:
                        from jina.flow import Flow
                        with Flow().add(uses=image.tags[0], daemon=self.args.daemon):
                            pass
                    except PeaFailToStart:
                        self.logger.error(f'can not use it in the Flow')
                        is_build_success = False

                if self.args.push:
                    try:
                        self.push(image.tags[0], self.readme_path)
                        is_push_success = True
                    except Exception:
                        self.logger.error(f'can not push to the registry')

            if self.args.prune_images:
                self.logger.info('deleting unused images')
                self._raw_client.prune_images()

            result = {
                'name': getattr(self, 'canonical_name', ''),
                'path': self.args.path,
                'details': _details,
                'last_build_time': get_now_timestamp(),
                'build_duration': tc.duration,
                'is_build_success': is_build_success,
                'is_push_success': is_push_success,
                'build_logs': _logs,
                'exception': _excepts
            }
        if not result['is_build_success'] and self.args.raise_error:
            # remove the very verbose build log when throw error
            result.pop('build_logs')
            raise RuntimeError(result)
        else:
            return result

    def dry_run(self) -> Dict:
        try:
            s = self._check_completeness()
            s['is_build_success'] = True
        except Exception as ex:
            s = {'is_build_success': False,
                 'exception': str(ex)}
        return s

    def _check_completeness(self) -> Dict:
        self.dockerfile_path = get_exist_path(self.args.path, 'Dockerfile')
        self.manifest_path = get_exist_path(self.args.path, 'manifest.yml')
        self.readme_path = get_exist_path(self.args.path, 'README.md')
        self.requirements_path = get_exist_path(self.args.path, 'requirements.txt')

        yaml_glob = glob.glob(os.path.join(self.args.path, '*.yml'))
        if yaml_glob:
            yaml_glob.remove(self.manifest_path)

        py_glob = glob.glob(os.path.join(self.args.path, '*.py'))

        test_glob = glob.glob(os.path.join(self.args.path, 'tests/test_*.py'))

        completeness = {
            'Dockerfile': self.dockerfile_path,
            'manifest.yml': self.manifest_path,
            'README.md': self.readme_path,
            'requirements.txt': self.requirements_path,
            '*.yml': yaml_glob,
            '*.py': py_glob,
            'tests': test_glob
        }

        self.logger.info(
            f'completeness check\n' +
            '\n'.join('%4s %-20s %s' % (colored('✓', 'green') if v else colored('✗', 'red'), k, v) for k, v in
                      completeness.items()) + '\n')

        if completeness['Dockerfile'] and completeness['manifest.yml']:
            pass
        else:
            self.logger.critical('Dockerfile or manifest.yml is not given, can not build')
            raise FileNotFoundError('Dockerfile or manifest.yml is not given, can not build')

        tmp = self._read_manifest(self.manifest_path)
        self.dockerfile_path_revised = self._get_revised_dockerfile(self.dockerfile_path, tmp)
        self.canonical_name = safe_url_name(f'{_repo_prefix}' + '{type}.{kind}.{name}:{version}'.format(**tmp))
        return completeness

    def _read_manifest(self, path: str, validate: bool = True):
        with resource_stream('jina', '/'.join(('resources', 'hub-builder', 'manifest.yml'))) as fp:
            tmp = yaml.load(fp)  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

        with open(path) as fp:
            tmp.update(yaml.load(fp))

        if validate:
            self._validate_manifest(tmp)

        return tmp

    def _validate_manifest(self, manifest: Dict):
        required = {'name', 'type', 'version'}

        # check the required field in manifest
        for r in required:
            if r not in manifest:
                raise ValueError(f'{r} is missing in the manifest.yaml, it is required')

        # check if all fields are there
        for r in _allowed:
            if r not in manifest:
                self.logger.warning(f'{r} is missing in your manifest.yml, you may want to check it')

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
            elif v and isinstance(v, list):
                manifest[k] = ','.join(v)

        # show manifest key-values
        for k, v in manifest.items():
            self.logger.debug(f'{k}: {v}')

    def _get_revised_dockerfile(self, dockerfile_path: str, manifest: Dict):
        # modify dockerfile
        revised_dockerfile = []
        with open(dockerfile_path) as fp:
            for l in fp:
                revised_dockerfile.append(l)
                if l.startswith('FROM'):
                    revised_dockerfile.append('LABEL ')
                    revised_dockerfile.append(
                        ' \\      \n'.join(f'{_label_prefix}{k}="{v}"' for k, v in manifest.items()))

        f = tempfile.NamedTemporaryFile('w', delete=False).name
        with open(f, 'w', encoding='utf8') as fp:
            fp.writelines(revised_dockerfile)

        for k in revised_dockerfile:
            self.logger.debug(k)
        return f
