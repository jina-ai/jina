__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import glob
import json
import requests
import urllib.parse
import urllib.request
import webbrowser
from typing import Dict

from .checker import *
from .helper import Waiter, handle_dot_in_keys, credentials_file
from ..clients.python import ProgressBar
from ..excepts import PeaFailToStart, TimedOutException, DockerLoginFailed
from ..helper import colored, get_readable_size, get_now_timestamp, get_full_version, random_name, expand_dict
from ..logging import JinaLogger
from ..logging.profile import TimeContext
from .hubapi import _list, _push

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
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))
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

    def new(self) -> None:
        """Create a new executor using cookiecutter template """
        try:
            from cookiecutter.main import cookiecutter
        except (ImportError, ModuleNotFoundError):
            self.logger.critical('requires "cookiecutter" dependency, please install it via "pip install cookiecutter"')
            raise

        import click
        cookiecutter_template = self.args.template
        if self.args.type == 'app':
            cookiecutter_template = 'https://github.com/jina-ai/cookiecutter-jina.git'
        elif self.args.type == 'pod':
            cookiecutter_template = 'https://github.com/jina-ai/cookiecutter-jina-hub.git'

        try:
            cookiecutter(cookiecutter_template, overwrite_if_exists=self.args.overwrite,
                         output_dir=self.args.output_dir)
        except click.exceptions.Abort:
            self.logger.info('nothing is created, bye!')

    def login(self) -> None:
        """Login using Github Device flow to allow push access to Jina Hub Registry"""
        with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
            hubapi_yml = yaml.load(fp)
        
        client_id = hubapi_yml['github']['client_id']
        scope = hubapi_yml['github']['scope']
        device_code_url = hubapi_yml['github']['device_code_url']
        access_token_url = hubapi_yml['github']['access_token_url']
        grant_type = hubapi_yml['github']['grant_type']
        seconds_to_wait = hubapi_yml['github']['wait_time_for_access_token']
        
        headers = {'Accept': 'application/json'}
        code_request_body = {
            'client_id': client_id, 
            'scope': scope
        }
        try:
            self.logger.info('logging in via Github device flow!')
            response = requests.post(url=device_code_url,
                                     headers=headers,
                                     data=code_request_body)
            if response.status_code != requests.codes.ok:
                self.logger.error('cannot reach github server. please make sure you\'re connected to internet')
            
            code_response = response.json()
            device_code = code_response['device_code']
            user_code = code_response['user_code']
            verification_uri = code_response['verification_uri']
            
            self.logger.info(f'please go to {colored(verification_uri, "cyan", attrs=["underline"])} & enter code '
                             f'{colored(user_code, "cyan", attrs=["bold"])} to authorize jina to login via Github OAuth')
            access_request_body = {
                'client_id': client_id,
                'device_code': device_code,
                'grant_type': grant_type
            }
            
            with Waiter(seconds=seconds_to_wait, message='to fetch access token') as waiter:
                while True:
                    response = requests.post(url=access_token_url,
                                             headers=headers,
                                             data=access_request_body)
                    access_token_response = response.json()
                    if waiter.is_time_up:
                        raise TimedOutException(f'login operation failed. '
                                                f'waited for {seconds_to_wait} seconds before timing out.')
                    if 'error' in access_token_response and access_token_response['error'] == 'authorization_pending':
                        waiter.sleep(5)
                    if 'access_token' in access_token_response:
                        token = {
                            'access_token': access_token_response['access_token']
                        }
                        with open(credentials_file(), 'w') as cf:
                            yaml.dump(token, cf)
                        self.logger.info(f'successfully logged in!')
                        break
                  
        except KeyError as exp:
            self.logger.error(f'didnot get following key in response: {exp}')
        except Exception as exp:
            self.logger.error(f'login failed: {exp}')
    
    def list(self):
        self.logger.info(f'Listing executors from Jina Hub registry')
        response = _list(logger=self.logger, name=self.args.name, kind=self.args.kind, 
                         type_=self.args.type, keywords=self.args.keywords)
        return response
        
    def push(self, name: str = None, readme_path: str = None) -> None:
        """ A wrapper of docker push 
        - Checks for the tempfile, returns without push if it cannot find
        - Pushes to docker hub, returns withput writing to db if it fails
        - Writes to the db
        """
        name = name or self.args.name
        file_path = get_summary_path(name)
        if not os.path.isfile(file_path):
            self.logger.error(f'can not find the build summary file. '
                              f'please build the image before pushing and pass tag with the image name')
            return

        try:
            self._push_docker_hub(name, readme_path)
        except Exception as ex:
            self.logger.error(f'can not complete the push due to {repr(ex)}')
            return

        with open(file_path) as f:
            result = json.load(f)
        if result['is_build_success']:
            _push(logger=self.logger, summary=result)

    def _push_docker_hub(self, name: str = None, readme_path: str = None) -> None:
        """ Helper push function """
        check_registry(self.args.registry, name, _repo_prefix)
        self._check_docker_image(name)
        self._docker_login()
        with ProgressBar(task_name=f'pushing {name}', batch_unit='') as t:
            for line in self._client.images.push(name, stream=True, decode=True):
                t.update(1)
                if 'error' in line and 'authentication required' in line['error']:
                    raise DockerLoginFailed('user not logged in to docker.')
                self.logger.debug(line)
        self.logger.success(f'🎉 {name} is now published!')

        if False and readme_path:
            # unfortunately Docker Hub Personal Access Tokens cannot be used as they are not supported by the API
            _volumes = {os.path.dirname(os.path.abspath(readme_path)): {'bind': '/workspace'}}
            _env = {
                'DOCKERHUB_USERNAME': self.args.username,
                'DOCKERHUB_PASSWORD': self.args.password,
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

    def pull(self) -> None:
        """A wrapper of docker pull """
        check_registry(self.args.registry, self.args.name, _repo_prefix)
        try:
            self._docker_login()
            with TimeContext(f'pulling {self.args.name}', self.logger):
                image = self._client.images.pull(self.args.name)
            if isinstance(image, list):
                image = image[0]
            image_tag = image.tags[0] if image.tags else ''
            self.logger.success(
                f'🎉 pulled {image_tag} ({image.short_id}) uncompressed size: {get_readable_size(image.attrs["Size"])}')
        except Exception as ex:
            self.logger.error(f'can not pull image {self.args.name} from {self.args.registry} due to {repr(ex)}')

    def _check_docker_image(self, name: str) -> None:
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

    def _docker_login(self) -> None:
        """A wrapper of docker login """
        from docker.errors import APIError
        if self.args.username and self.args.password:
            try:
                self._client.login(username=self.args.username, password=self.args.password,
                                   registry=self.args.registry)
                self.logger.debug(f'successfully logged in to docker hub')
            except APIError:
                raise DockerLoginFailed(f'invalid credentials passed. docker login failed')
        else:
            raise DockerLoginFailed('no username/password specified, docker login failed')

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
                        tag=self.tag,
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
                                                       tag=self.tag,
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
                        is_build_success = False
                        from jina.flow import Flow
                        p_name = random_name()
                        with Flow().add(name=p_name, uses=image.tags[0], daemon=self.args.daemon):
                            pass
                        if self.args.daemon:
                            self._raw_client.stop(p_name)
                        self._raw_client.prune_containers()
                        is_build_success = True
                    except PeaFailToStart:
                        self.logger.error(f'can not use it in the Flow, please check your file bundle')
                    except Exception as ex:
                        self.logger.error(f'something wrong but it is probably not your fault. {repr(ex)}')

                _version = self.manifest['version'] if 'version' in self.manifest else '0.0.1'
                info, env_info = get_full_version()
                _host_info = {
                    'jina': info,
                    'jina_envs': env_info,
                    'docker': self._raw_client.info(),
                    'build_args': vars(self.args)
                }

            _build_history = {
                'time': get_now_timestamp(),
                'host_info': _host_info if is_build_success and self.args.host_info else '',
                'duration': tc.readable_duration,
                'logs': _logs,
                'exception': _excepts
            }

            if self.args.prune_images:
                self.logger.info('deleting unused images')
                self._raw_client.prune_images()

            result = {
                'name': getattr(self, 'canonical_name', ''),
                'version': self.manifest['version'] if is_build_success and 'version' in self.manifest else '0.0.1',
                'path': self.args.path,
                'manifest_info': self.manifest if is_build_success else '',
                'details': _details,
                'is_build_success': is_build_success,
                'build_history': [_build_history]
            }

            # only successful build (NOT dry run) writes the summary to disk
            if result['is_build_success']:
                self._write_summary_to_file(summary=result)
                if self.args.push:
                    try:
                        self._push_docker_hub(image.tags[0], self.readme_path)
                        _push(logger=self.logger, summary=result)
                        self._write_slack_message(result, _details, _build_history)
                    except Exception as ex:
                        self.logger.error(f'can not complete the push due to {repr(ex)}')

        if not result['is_build_success'] and self.args.raise_error:
            # remove the very verbose build log when throw error
            result['build_history'][0].pop('logs')
            raise RuntimeError(result)

        return result

    def dry_run(self) -> Dict:
        try:
            s = self._check_completeness()
            s['is_build_success'] = True
        except Exception as ex:
            s = {'is_build_success': False,
                 'exception': str(ex)}
        return s

    def _write_summary_to_file(self, summary: Dict) -> None:
        file_path = get_summary_path(f'{summary["name"]}:{summary["version"]}')
        with open(file_path, 'w+') as f:
            json.dump(summary, f)
        self.logger.debug(f'stored the summary from build to {file_path}')

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

        self.manifest = self._read_manifest(self.manifest_path)
        self.dockerfile_path_revised = self._get_revised_dockerfile(self.dockerfile_path, self.manifest)
        self.tag = safe_url_name(f'{_repo_prefix}' + '{type}.{kind}.{name}:{version}'.format(**self.manifest))
        self.canonical_name = safe_url_name(f'{_repo_prefix}' + '{type}.{kind}.{name}'.format(**self.manifest))
        return completeness

    def _read_manifest(self, path: str, validate: bool = True) -> Dict:
        with resource_stream('jina', '/'.join(('resources', 'hub-builder', 'manifest.yml'))) as fp:
            tmp = yaml.load(fp)  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

        with open(path) as fp:
            tmp.update(yaml.load(fp))

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

        # show manifest key-values
        for k, v in manifest.items():
            self.logger.debug(f'{k}: {v}')

    def _get_revised_dockerfile(self, dockerfile_path: str, manifest: Dict) -> str:
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

    def _write_slack_message(self, *args):
        def _expand_fn(v):
            if isinstance(v, str):
                for d in args:
                    try:
                        v = v.format(**d)
                    except KeyError:
                        pass
            return v

        if 'JINAHUB_SLACK_WEBHOOK' in os.environ:
            with resource_stream('jina', '/'.join(('resources', 'hub-builder-success', 'slack-jinahub.json'))) as fp:
                tmp = expand_dict(json.load(fp), _expand_fn, resolve_cycle_ref=False)
                req = urllib.request.Request(os.environ['JINAHUB_SLACK_WEBHOOK'])
                req.add_header('Content-Type', 'application/json; charset=utf-8')
                jdb = json.dumps(tmp).encode('utf-8')  # needs to be bytes
                req.add_header('Content-Length', str(len(jdb)))
                with urllib.request.urlopen(req, jdb) as f:
                    res = f.read()
                    self.logger.info(f'push to Slack: {res}')

    # alias of "new" in cli
    create = new
    init = new
