"""Module for wrapping Jina Hub API calls."""

from jina.hubble.hubapi import JINA_HUB_ROOT
import os
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin
import hashlib
from ..helper import (
    colored,
    get_full_version,
    get_readable_size,
)
from ..importer import ImportExtensions
from ..logging.logger import JinaLogger
from ..logging.profile import TimeContext
from .helper import archive_package, download_with_resume
from .hubapi import install_locall


JINA_HUBBLE_REGISTRY = os.environ.get(
    'JINA_HUBBLE_REGISTRY', 'https://apihubble.jina.ai'
)
JINA_HUBBLE_PUSHPULL_URL = urljoin(JINA_HUBBLE_REGISTRY, '/v1/executors')


class HubIO:
    """:class:`HubIO` provides the way to interact with Jina Hub registry.
    You can use it with CLI to package a directory into a Jina Hub and publish it to the world.
    Examples:
        - :command:`jina hub push my_executor/` to push the executor package to Jina Hub
        - :command:`jina hub pull UUID8` to download the executor identified by UUID8
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
                'public': self.args.public,
                'private': self.args.private,
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

            else:
                resp.raise_for_status()

        except Exception as e:  # IO related errors
            self.logger.error(
                f'Error when trying to push the executor at {self.args.path}: {e!r}'
            )

    def pull(self) -> None:
        """Pull the executor pacakge from Jina Hub."""

        import requests

        pull_url = JINA_HUBBLE_PUSHPULL_URL + f'/{self.args.id}'
        if self.args.secret:
            pull_url += f'?secret={self.args.secret}'

        try:
            resp = requests.get(pull_url)

            if resp.status_code == 200:
                msg = resp.json()

                if not self.args.docker:
                    # download the package
                    pass
                else:
                    # pull the Docker image
                    image_name = msg['pullPath']

                    # # TODO: only for test
                    # image_name = 'jinahub/pod.dummy_mwu_encoder:0.0.6'

                    with TimeContext(f'pulling {image_name}', self.logger):
                        image = self._client.images.pull(image_name)
                    if isinstance(image, list):
                        image = image[0]
                    image_tag = image.tags[0] if image.tags else ''
                    self.logger.success(
                        f'🎉 pulled {image_tag} ({image.short_id}) uncompressed size: {get_readable_size(image.attrs["Size"])}'
                    )
            else:
                resp.raise_for_status()

        except Exception as e:
            self.logger.error(
                f'Error when trying to pull the executor: {self.args.id}: {e!r}'
            )
