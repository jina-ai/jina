"""Module for wrapping Jina Hub API calls."""


from jina.parsers.hubble import pull
import os
import argparse
import json
from pathlib import Path
from typing import Optional
from collections import namedtuple
from urllib.parse import urljoin, urlencode
import hashlib
from ..helper import (
    colored,
    get_full_version,
    get_readable_size,
)
from ..importer import ImportExtensions
from ..logging.logger import JinaLogger
from ..logging.profile import TimeContext
from ..excepts import HubDownloadError
from .helper import archive_package, download_with_resume, parse_hub_uri
from .hubapi import install_local, exist_local
from . import JINA_HUB_ROOT, JINA_HUB_CACHE_DIR

JINA_HUBBLE_REGISTRY = os.environ.get(
    'JINA_HUBBLE_REGISTRY', 'https://apihubble.jina.ai'
)
JINA_HUBBLE_PUSHPULL_URL = urljoin(JINA_HUBBLE_REGISTRY, '/v1/executors')

HubExecutor = namedtuple(
    'HubExecutor',
    ['id', 'current_tag', 'visibility', 'image_name', 'archive_url', 'md5sum'],
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

    def __init__(self, args: 'argparse.Namespace'):
        self.logger = JinaLogger(self.__class__.__name__, **vars(args))
        self.args = args
        self._load_docker_client()

    def _load_docker_client(self):
        with ImportExtensions(
            required=True,
            help_text='missing "docker" dependency, please do pip install "jina[docker]"',
        ):
            import docker
            from docker import APIClient, DockerClient

            self._client: DockerClient = docker.from_env()

            # low-level client
            self._raw_client = APIClient(base_url='unix://var/run/docker.sock')

    def push(self) -> None:
        """Push the executor pacakge to Jina Hub."""

        import requests

        pkg_path = Path(self.args.path)
        if not pkg_path.exists():
            self.logger.critical(
                f'The folder "{self.args.path}" does not exist, can not push'
            )
            exit(1)

        try:
            # archive the executor package
            with TimeContext(f'archiving {self.args.path}', self.logger):
                md5_hash = hashlib.md5()
                bytesio = archive_package(pkg_path)
                content = bytesio.getvalue()
                md5_hash.update(content)

                md5_digest = md5_hash.hexdigest()

            # upload the archived package
            meta, env = get_full_version()
            form_data = {
                'meta': json.dumps(meta),
                'env': json.dumps(env),
                'public': self.args.public if hasattr(self.args, 'public') else False,
                'private': self.args.private
                if hasattr(self.args, 'private')
                else False,
                'md5sum': md5_digest,
                'force': self.args.force,
                'secret': self.args.secret,
            }

            method = 'put' if self.args.force else 'post'
            # upload the archived executor to Jina Hub
            with TimeContext(
                f'uploading to {method.upper()} {JINA_HUBBLE_PUSHPULL_URL}', self.logger
            ):
                request = getattr(requests, method)
                resp = request(
                    JINA_HUBBLE_PUSHPULL_URL,
                    files={'file': content},
                    data=form_data,
                )

            if 200 <= resp.status_code < 300:
                # TODO: only support single executor now
                image = resp.json()['executors'][0]

                uuid8 = image['id']
                secret = image['secret']
                docker_image = image['pullPath']
                visibility = image['visibility']
                usage = (
                    f'jinahub://{uuid8}'
                    if visibility == 'public'
                    else f'jinahub://{uuid8}:{secret}'
                )

                info_table = [
                    f'\t🔑 ID:\t\t' + colored(f'{uuid8}', 'cyan'),
                    f'\t🔒 Secret:\t'
                    + colored(
                        f'{secret}',
                        'cyan',
                    ),
                    f'\t🐳 Image:\t' + colored(f'{docker_image}', 'cyan'),
                    f'\t👀 Visibility:\t' + colored(f'{visibility}', 'cyan'),
                ]
                self.logger.success(
                    f'🎉 The executor at {pkg_path} is now published successfully!'
                )
                self.logger.info('\n' + '\n'.join(info_table))
                self.logger.info(
                    'You can use this Executor in the Flow via '
                    + colored(usage, 'cyan', attrs='underline')
                )

            elif resp.text:
                # NOTE: sometimes resp.text returns empty
                raise Exception(resp.text)
            else:
                resp.raise_for_status()

        except Exception as e:  # IO related errors
            self.logger.error(
                f'Error when trying to push the executor at {self.args.path}: {e!r}'
            )

    def fetch(
        self, id: str, tag: Optional[str] = None, secret: Optional[str] = None
    ) -> HubExecutor:
        """Fetch the executor meta info from Jina Hub.
        :param id: the ID of the executor
        :param tag: the version tag of the executor
        :param secret: the access secret of the executor
        :return: meta of executor
        """
        with ImportExtensions(required=True):
            import requests

        pull_url = JINA_HUBBLE_PUSHPULL_URL + f'/{id}/?'
        path_params = {}
        if secret:
            path_params['secret'] = secret
        if tag:
            path_params['tag'] = tag

        pull_url += urlencode(path_params)
        resp = requests.get(pull_url)
        if resp.status_code != 200:
            if resp.text:
                raise Exception(resp.text)
            resp.raise_for_status()

        resp = resp.json()
        assert resp['id'] == id

        result = HubExecutor(
            resp['id'],
            f'v{resp["currentVersion"]}',
            resp['visibility'],
            resp['pullPath'],
            resp['package']['download'],
            resp['package']['md5'],
        )

        return result

    def pull(self) -> None:
        """Pull the executor package from Jina Hub."""
        cached_zip_filepath = None
        try:
            scheme, uuid, tag, secret = parse_hub_uri(self.args.uri)

            if scheme not in ['jinahub', 'jinahub+docker']:
                raise ValueError(f'Unkonwn schema: {scheme}')

            executor = self.fetch(uuid, tag=tag, secret=secret)

            if not tag:
                tag = executor.current_tag

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
                self.logger.warning(
                    f'The executor {self.args.uri} has already been downloaded in {JINA_HUB_ROOT}'
                )
                return

            # download the package
            with TimeContext(f'downloading {self.args.uri}', self.logger):
                cached_zip_filename = f'{uuid}-{md5sum}.zip'
                cached_zip_filepath = download_with_resume(
                    archive_url,
                    JINA_HUB_CACHE_DIR,
                    cached_zip_filename,
                    md5sum=md5sum,
                )

            with TimeContext(f'installing {self.args.uri}', self.logger):
                try:
                    install_local(cached_zip_filepath, uuid, tag)
                except Exception as ex:
                    raise HubDownloadError(str(ex))

        except Exception as e:
            self.logger.error(
                f'Error when trying to pull the executor: {self.args.uri}: {e!r}'
            )
        finally:
            # delete downloaded zip package if existed
            if cached_zip_filepath is not None:
                cached_zip_filepath.unlink(missing_ok=True)
