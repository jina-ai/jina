"""Module for wrapping Jina Hub API calls."""

import argparse
import hashlib
import json
import os
from collections import namedtuple
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlencode

from .helper import (
    archive_package,
    download_with_resume,
    parse_hub_uri,
    get_hubble_url,
    upload_file,
)
from .hubapi import install_local, resolve_local, load_secret, dump_secret, get_lockfile
from ..helper import get_full_version, ArgNamespace
from ..importer import ImportExtensions
from ..logging.logger import JinaLogger
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

        with ImportExtensions(required=True):
            import rich
            import cryptography
            import filelock

            assert rich  #: prevent pycharm auto remove the above line
            assert cryptography
            assert filelock

    def _load_docker_client(self):
        with ImportExtensions(required=True):
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

        from rich.console import Console

        console = Console()
        with console.status(f'Pushing `{self.args.path}`...') as st:
            req_header = self._get_request_header()
            try:
                st.update(f'Packaging {self.args.path}...')
                md5_hash = hashlib.md5()
                bytesio = archive_package(Path(self.args.path))
                content = bytesio.getvalue()
                md5_hash.update(content)
                md5_digest = md5_hash.hexdigest()

                # upload the archived package
                form_data = {
                    'public': 'True' if getattr(self.args, 'public', None) else 'False',
                    'private': 'True'
                    if getattr(self.args, 'private', None)
                    else 'False',
                    'md5sum': md5_digest,
                }
                uuid8, secret = load_secret(Path(self.args.path))
                if self.args.force or uuid8:
                    form_data['force'] = self.args.force or uuid8
                if self.args.secret or secret:
                    form_data['secret'] = self.args.secret or secret

                method = 'put' if ('force' in form_data) else 'post'

                st.update(f'Connecting Hubble...')
                hubble_url = get_hubble_url()
                # upload the archived executor to Jina Hub

                st.update(f'Uploading...')
                resp = upload_file(
                    hubble_url,
                    'filename',
                    content,
                    dict_data=form_data,
                    headers=req_header,
                    stream=True,
                    method=method,
                )

                result = None
                for stream_line in resp.iter_lines():
                    stream_msg = json.loads(stream_line)
                    if 'stream' in stream_msg:
                        st.update(stream_msg['stream'])
                    elif 'result' in stream_msg:
                        result = stream_msg['result']
                        break

                if result is None:
                    raise Exception('Unknown Error')
                elif not result.get('data', None):
                    raise Exception(result.get('message', 'Unknown Error'))
                elif 200 <= result['statusCode'] < 300:
                    new_uuid8, new_secret = self._prettyprint_result(console, result)
                    if new_uuid8 != uuid8 or new_secret != secret:
                        dump_secret(Path(self.args.path), new_uuid8, new_secret)
                elif result['message']:
                    raise Exception(result['message'])
                elif resp.text:
                    # NOTE: sometimes resp.text returns empty
                    raise Exception(resp.text)
                else:
                    resp.raise_for_status()

            except Exception as e:  # IO related errors
                self.logger.error(
                    f'Error while pushing session_id={req_header["jinameta-session-id"]}: '
                    f'\n{e!r}'
                )
                raise e

    def _prettyprint_result(self, console, result):
        # TODO: only support single executor now

        from rich.table import Table
        from rich import box

        data = result.get('data', None)
        image = data['executors'][0]
        uuid8 = image['id']
        secret = image['secret']
        visibility = image['visibility']

        table = Table(box=box.SIMPLE)
        table.add_column('Key', no_wrap=True)
        table.add_column('Value', style='cyan', no_wrap=True)
        table.add_row(':key: ID', uuid8)
        if 'alias' in image:
            table.add_row(':name_badge: Alias', image['alias'])
        table.add_row(':lock: Secret', secret)
        table.add_row(
            '',
            ':point_up:️ [bold red]Please keep this token in a safe place!',
        )
        table.add_row(':eyes: Visibility', visibility)
        table.add_row(':whale: DockerHub', f'https://hub.docker.com/r/jinahub/{uuid8}/')
        console.print(table)

        presented_id = image.get('alias', uuid8)
        usage = (
            f'{presented_id}' if visibility == 'public' else f'{presented_id}:{secret}'
        )

        if not self.args.no_usage:
            self._get_prettyprint_usage(console, usage)

        return uuid8, secret

    def _get_prettyprint_usage(self, console, usage):
        from rich.panel import Panel
        from rich.syntax import Syntax

        flow_plain = f'''from jina import Flow

f = Flow().add(uses='jinahub://{usage}')

with f:
    ...'''

        flow_docker = f'''from jina import Flow

f = Flow().add(uses='jinahub+docker://{usage}')

with f:
    ...'''

        cli_plain = f'jina executor --uses jinahub://{usage}'

        cli_docker = f'jina executor --uses jinahub+docker://{usage}'

        p1 = Panel(
            Syntax(
                flow_plain, 'python', theme='monokai', line_numbers=True, word_wrap=True
            ),
            title='Flow usage',
            width=80,
            expand=False,
        )
        p2 = Panel(
            Syntax(
                flow_docker,
                'python',
                theme='monokai',
                line_numbers=True,
                word_wrap=True,
            ),
            title='Flow usage via Docker',
            width=80,
            expand=False,
        )

        p3 = Panel(
            Syntax(
                cli_plain, 'console', theme='monokai', line_numbers=True, word_wrap=True
            ),
            title='CLI usage',
            width=80,
            expand=False,
        )
        p4 = Panel(
            Syntax(
                cli_docker,
                'console',
                theme='monokai',
                line_numbers=True,
                word_wrap=True,
            ),
            title='CLI usage via Docker',
            width=80,
            expand=False,
        )

        console.print(p1, p2, p3, p4)

    @staticmethod
    def _fetch_meta(
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
        if path_params:
            pull_url += urlencode(path_params)

        resp = requests.get(pull_url, headers=HubIO._get_request_header())
        if resp.status_code != 200:
            if resp.text:
                raise Exception(resp.text)
            resp.raise_for_status()

        resp = resp.json()

        return HubExecutor(
            resp['id'],
            resp.get('alias', None),
            resp['tag'],
            resp['visibility'],
            resp['image'],
            resp['package']['download'],
            resp['package']['md5'],
        )

    def pull(self) -> str:
        """Pull the executor package from Jina Hub.

        :return: the `uses` string
        """
        from rich.console import Console

        console = Console()
        cached_zip_filepath = None
        usage = None

        with console.status(f'Pulling {self.args.uri}...') as st:
            try:
                scheme, name, tag, secret = parse_hub_uri(self.args.uri)

                st.update('Fetching meta data...')
                executor = HubIO._fetch_meta(name, tag=tag, secret=secret)
                usage = (
                    f'{executor.uuid}'
                    if executor.visibility == 'public'
                    else f'{executor.uuid}:{secret}'
                )

                if scheme == 'jinahub+docker':
                    self._load_docker_client()
                    st.update(f'Pulling {executor.image_name}...')
                    self._client.images.pull(executor.image_name)
                    return f'docker://{executor.image_name}'
                elif scheme == 'jinahub':
                    import filelock

                    with filelock.FileLock(get_lockfile(), timeout=-1):
                        try:
                            pkg_path = resolve_local(executor.uuid, tag or executor.tag)
                            return f'{pkg_path / "config.yml"}'
                        except FileNotFoundError:
                            pass  # have not been downloaded yet, download for the first time

                        # download the package
                        cache_dir = Path(
                            os.environ.get(
                                'JINA_HUB_CACHE_DIR',
                                Path.home().joinpath('.cache', 'jina'),
                            )
                        )
                        cache_dir.mkdir(parents=True, exist_ok=True)

                        st.update(f'Downloading...')
                        cached_zip_filepath = download_with_resume(
                            executor.archive_url,
                            cache_dir,
                            f'{executor.uuid}-{executor.md5sum}.zip',
                            md5sum=executor.md5sum,
                        )

                        st.update(f'Unpacking...')
                        install_local(
                            cached_zip_filepath,
                            executor.uuid,
                            tag or executor.tag,
                            install_deps=self.args.install_requirements,
                        )

                        pkg_path = resolve_local(executor.uuid, tag or executor.tag)
                        return f'{pkg_path / "config.yml"}'
                else:
                    raise ValueError(f'{self.args.uri} is not a valid scheme')
            except Exception as e:
                self.logger.error(f'{e!r}')
                raise e
            finally:
                # delete downloaded zip package if existed
                if cached_zip_filepath is not None:
                    cached_zip_filepath.unlink()

                if not self.args.no_usage and usage:
                    self._get_prettyprint_usage(console, usage)
