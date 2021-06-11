"""Module for wrapping Jina Hub API calls."""

import os
import argparse
from pathlib import Path

from ..helper import (
    colored,
    get_full_version,
)
from ..logging.logger import JinaLogger
from ..logging.profile import TimeContext
from .helper import archive_package


HUBBLE_REGISTRY = os.environ.get('HUBBLE_REGISTRY', 'https://hubble.jina.ai')


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
        import hashlib

        is_public = True
        if self.args.private:
            is_public = False
            self.args.public = False

        pkg_path = Path(self.args.path)
        if not pkg_path.exists():
            self.logger.critical(
                f'The folder "{self.args.path}" does not exist, can not push'
            )
            raise FileNotFoundError(
                f'The folder "{self.args.path}" does not exist, can not push'
            )

        try:
            # archive the executor package
            with TimeContext(f'archiving executor at {self.args.path}', self.logger):
                md5_hash = hashlib.md5()
                bytesio = archive_package(pkg_path)
                content = bytesio.getvalue()
                md5_hash.update(content)

                md5_digest = md5_hash.hexdigest()

            # upload the archived package
            payload = {
                "meta": get_full_version(),
                'is_public': is_public,
                'md5sum': md5_digest,
                'force': self.args.force,
                'secret': self.args.secret,
            }

            # upload the archived executor to Jina Hub
            upload_url = HUBBLE_REGISTRY + '/upload'
            with TimeContext(f'uploading to {upload_url}', self.logger):
                resp = requests.post(upload_url, files={'file': content}, data=payload)

            if resp.status_code == 201 and resp.json()['success']:
                # TODO: better logging info
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

        self.logger.success(f'🎉 The executor located at {pkg_path} is now published!')
