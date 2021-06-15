"""Module for wrapping Jina Hub API calls."""

import os
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin
import hashlib
from ..helper import (
    colored,
    get_full_version,
)
from ..logging.logger import JinaLogger
from ..logging.profile import TimeContext
from .helper import archive_package


JINA_HUBBLE_REGISTRY = os.environ.get('JINA_HUBBLE_REGISTRY', 'https://hubble.jina.ai')
JINA_HUBBLE_PUSH_URL = urljoin(JINA_HUBBLE_REGISTRY, '/v1/executors/push')


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
                'is_public': self.args.public,
                'md5sum': md5_digest,
                'force': self.args.force,
                'secret': self.args.secret,
            }

            # upload the archived executor to Jina Hub
            with TimeContext(f'uploading to {JINA_HUBBLE_PUSH_URL}', self.logger):
                resp = requests.post(
                    JINA_HUBBLE_PUSH_URL, files={'file': content}, data=form_data
                )

            if resp.status_code == 201:
                if resp.json()['success']:
                    # TODO: only support single executor now
                    image = resp.json()['data']['images'][0]

                    uuid8 = image['id']
                    secret = image['secret']
                    docker_image = image['pullPath']

                    info_table = [
                        f'\t🔑 ID:\t' + colored(f'{uuid8}', 'cyan'),
                        f'\t🔒 Secret:\t'
                        + colored(
                            f'{secret}',
                            'cyan',
                        ),
                        f'\t🐳 Image:\t' + colored(f'{docker_image}', 'cyan'),
                    ]
                    self.logger.success(
                        f'🎉 The executor at {pkg_path} is now published successfully!'
                    )
                    self.logger.info('\n' + '\n'.join(info_table))
                    self.logger.info(
                        'You can use this Executor in the Flow via '
                        + colored(f'jinahub://{uuid8}', 'cyan', attrs='underline')
                    )

            else:
                raise Exception(resp.text)

        except Exception as e:  # IO related errors
            self.logger.error(
                f'Error when trying to push the executor at {self.args.path}: {e!r}'
            )
