"""Module for wrapping Jina Hub API calls."""

import argparse
import hashlib
import os
import json
from collections import namedtuple
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlencode

from .helper import archive_package, download_with_resume, parse_hub_uri, get_hubble_url
from .hubapi import install_local, exist_local
from .progress_bar import ProgressBar
from ..excepts import HubDownloadError
from ..helper import colored, get_full_version, get_readable_size, ArgNamespace
from ..importer import ImportExtensions
from ..logging.logger import JinaLogger
from ..logging.profile import TimeContext
from ..parsers.hubble import set_hub_parser

HubExecutor = namedtuple(
    'HubExecutor',
    ['uuid', 'alias', 'tag', 'visibility', 'image_name', 'archive_url', 'md5sum'],
)


class HubIO:
    """:class:`HubIO` provides the way to interact with Jina Hub registry.
    You can use it with CLI to package a directory into a Jina Hub and publish it to the world.
    Examples:
        - :command:`jina hub push my_executor/` to push the executor package to Jina Hub
        - :command:`jina hub pull UUID8` to download the executor identified by UUID8

    To create a :class:`HubIO` object, simply:

        .. highlight:: python
        .. code-block:: python
            hubio = HubIO(args)

    :param args: arguments
    """

    def __init__(self, args: Optional[argparse.Namespace] = None, **kwargs):
        if args and isinstance(args, argparse.Namespace):
            self.args = args
        else:
            self.args = ArgNamespace.kwargs2namespace(kwargs, set_hub_parser())
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))

        self._load_docker_client()

    def _load_docker_client(self):
        with ImportExtensions(
            required=True,
            help_text='missing "docker" dependency, please do pip install "jina[docker]"',
        ):
            import docker
            from docker import DockerClient

            self._client: DockerClient = docker.from_env()

    @staticmethod
    def _get_request_header() -> Dict:
        """Return the header of request.

        :return: request header
        """
        metas, envs = get_full_version()

        header = {
            **{f'jinameta-{k}': str(v) for k, v in metas.items()},
            **envs,
        }
        return header

    def push(self) -> None:
        """Push the executor pacakge to Jina Hub."""

        with ImportExtensions(required=True):
            import requests

        pkg_path = Path(self.args.path)
        if not pkg_path.exists():
            self.logger.critical(f'`{self.args.path}` is not a valid path!')
            exit(1)

        request_headers = self._get_request_header()

        try:
            # archive the executor package
            with TimeContext(f'Packaging {self.args.path}', self.logger):
                md5_hash = hashlib.md5()
                bytesio = archive_package(pkg_path)
                content = bytesio.getvalue()
                md5_hash.update(content)
                md5_digest = md5_hash.hexdigest()

            # upload the archived package
            form_data = {
                'public': 'True' if getattr(self.args, 'public', None) else 'False',
                'private': 'True' if getattr(self.args, 'private', None) else 'False',
                'md5sum': md5_digest,
            }
            if self.args.force:
                form_data['force'] = self.args.force
            if self.args.secret:
                form_data['secret'] = self.args.secret

            method = 'put' if self.args.force else 'post'

            hubble_url = get_hubble_url()
            # upload the archived executor to Jina Hub
            with TimeContext(
                f'Pushing to {hubble_url} ({method.upper()})',
                self.logger,
            ):
                from .helper import upload_file

                resp = upload_file(
                    hubble_url,
                    'filename',
                    content,
                    dict_data=form_data,
                    headers=request_headers,
                    stream=True,
                    method=method,
                )

                result = None
                for stream_line in resp.iter_lines():
                    stream_msg = json.loads(stream_line)
                    if 'stream' in stream_msg:
                        self.logger.info(stream_msg['stream'])
                    elif 'result' in stream_msg:
                        result = stream_msg['result']
                        break

                if result is None:
                    raise Exception('Unknown Error')

                if 200 <= result['statusCode'] < 300:
                    # TODO: only support single executor now
                    data = result.get('data', None)
                    if not data:
                        raise Exception(result.get('message', 'Unknown Error'))

                    image = data['executors'][0]

                    uuid8 = image['id']
                    secret = image['secret']
                    visibility = image['visibility']

                    info_table = [
                        f'\t🔑 ID:\t\t' + colored(f'{uuid8}', 'cyan'),
                        f'\t🔒 Secret:\t'
                        + colored(
                            f'{secret}',
                            'cyan',
                        )
                        + colored(
                            ' (👈 Please store this secret carefully, it wont show up again)',
                            'red',
                        ),
                        f'\t👀 Visibility:\t' + colored(f'{visibility}', 'cyan'),
                    ]

                    if 'alias' in image:
                        info_table.append(
                            f'\t📛 Alias:\t' + colored(image['alias'], 'cyan')
                        )

                    self.logger.success(
                        f'🎉 Executor `{pkg_path}` is pushed successfully!'
                    )
                    self.logger.info('\n' + '\n'.join(info_table))

                    usage = (
                        f'jinahub://{uuid8}'
                        if visibility == 'public'
                        else f'jinahub://{uuid8}:{secret}'
                    )

                    self.logger.info(
                        f'You can use it via `uses={usage}` in the Flow/CLI.'
                    )
                elif result['message']:
                    raise Exception(result['message'])
                elif resp.text:
                    # NOTE: sometimes resp.text returns empty
                    raise Exception(resp.text)
                else:
                    resp.raise_for_status()
        except Exception as e:  # IO related errors
            self.logger.error(
                f'Error while pushing `{self.args.path}` with session_id={request_headers["jinameta-session-id"]}: '
                f'\n{e!r}'
            )

    @staticmethod
    def fetch(
        name: str,
        tag: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> HubExecutor:
        """Fetch the executor meta info from Jina Hub.
        :param name: the UUID/Alias of the executor
        :param tag: the version tag of the executor
        :param secret: the access secret of the executor
        :return: meta of executor
        """

        with ImportExtensions(required=True):
            import requests

        pull_url = get_hubble_url() + f'/{name}/?'
        path_params = {}
        if secret:
            path_params['secret'] = secret
        if tag:
            path_params['tag'] = tag

        request_headers = HubIO._get_request_header()

        pull_url += urlencode(path_params)
        resp = requests.get(pull_url, headers=request_headers)
        if resp.status_code != 200:
            if resp.text:
                raise Exception(resp.text)
            resp.raise_for_status()

        resp = resp.json()

        result = HubExecutor(
            resp['id'],
            resp.get('alias', None),
            resp['tag'],
            resp['visibility'],
            resp['image'],
            resp['package']['download'],
            resp['package']['md5'],
        )

        return result

    def pull(self) -> None:
        """Pull the executor package from Jina Hub."""
        cached_zip_filepath = None
        try:
            scheme, name, tag, secret = parse_hub_uri(self.args.uri)

            executor = HubIO.fetch(name, tag=tag, secret=secret)

            if not tag:
                tag = executor.tag

            uuid = executor.uuid
            image_name = executor.image_name
            archive_url = executor.archive_url
            md5sum = executor.md5sum

            if scheme == 'jinahub+docker':
                # pull the Docker image
                with TimeContext(f'pulling {image_name}', self.logger):
                    image = self._client.images.pull(image_name)
                if isinstance(image, list):
                    image = image[0]
                image_tag = image.tags[0] if image.tags else ''
                self.logger.success(
                    f'🎉 pulled {image_tag} ({image.short_id}) uncompressed size: {get_readable_size(image.attrs["Size"])}'
                )
                return
            if exist_local(uuid, tag):
                self.logger.debug(
                    f'The executor `{self.args.uri}` has already been downloaded.'
                )
                return
            # download the package
            with TimeContext(f'downloading {self.args.uri}', self.logger):
                cache_dir = Path(
                    os.environ.get(
                        'JINA_HUB_CACHE_DIR', Path.home().joinpath('.cache', 'jina')
                    )
                )
                cache_dir.mkdir(parents=True, exist_ok=True)
                cached_zip_filename = f'{uuid}-{md5sum}.zip'
                cached_zip_filepath = download_with_resume(
                    archive_url,
                    cache_dir,
                    cached_zip_filename,
                    md5sum=md5sum,
                )

            with TimeContext(f'unpacking {self.args.uri}', self.logger):
                try:
                    install_local(
                        cached_zip_filepath,
                        uuid,
                        tag,
                        install_deps=self.args.install_requirements,
                    )
                except Exception as ex:
                    raise HubDownloadError(str(ex))

        except Exception as e:
            self.logger.error(
                f'Error when pulling the executor `{self.args.uri}`: {e!r}'
            )
        finally:
            # delete downloaded zip package if existed
            if cached_zip_filepath is not None:
                cached_zip_filepath.unlink()
