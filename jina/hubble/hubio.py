"""Module for wrapping Jina Hub API calls."""

import argparse
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlencode

from . import HubExecutor
from .helper import (
    archive_package,
    download_with_resume,
    parse_hub_uri,
    get_hubble_url,
    upload_file,
    disk_cache_offline,
)
from .helper import install_requirements
from .hubapi import install_local, resolve_local, load_secret, dump_secret, get_lockfile
from .. import __resources_path__
from ..helper import get_full_version, ArgNamespace
from ..importer import ImportExtensions
from ..logging.logger import JinaLogger
from ..parsers.hubble import set_hub_parser

_cache_file = Path.home().joinpath('.jina', 'disk_cache.db')


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
            from docker import APIClient

            try:
                # low-level client
                self._raw_client = APIClient(base_url='unix://var/run/docker.sock')
            except docker.errors.DockerException:
                self.logger.critical(
                    f'Docker daemon seems not running. Please run Docker daemon and try again.'
                )
                exit(1)

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

    def new(self) -> None:
        """Create a new executor folder interactively."""

        from rich import print, box
        from rich.prompt import Prompt, Confirm
        from rich.panel import Panel
        from rich.table import Table
        from rich.console import Console
        from rich.progress import track
        from rich.syntax import Syntax

        console = Console()

        print(
            Panel.fit(
                '''
[bold green]Executor[/bold green] is how Jina processes [bold]Document[/bold]. 

This guide helps you to create your own Executor in 30 seconds.''',
                title='Create New Executor',
            )
        )

        exec_name = Prompt.ask(
            ':grey_question: What is the [bold]name[/bold] of your executor?\n'
            '[dim]CamelCase is required[/dim]',
            default=f'MyExecutor{random.randint(0, 100)}',
        )

        exec_path = Prompt.ask(
            ':grey_question: [bold]Which folder[/bold] to store your executor?',
            default=os.path.join(os.getcwd(), exec_name),
        )

        exec_description = '{{}}'
        exec_keywords = '{{}}'
        exec_url = '{{}}'

        is_dockerfile = False

        if Confirm.ask(
            '[green]That\'s all we need to create an Executor![/green]\n'
            ':grey_question: Or do you want to proceed to advanced configuration',
            default=False,
        ):
            exec_description = (
                Prompt.ask(
                    ':grey_question: Please give a [bold]short description[/bold] of your executor?\n'
                    f'[dim]Example: {exec_name} embeds images into 128-dim vectors using ResNet.[/dim]'
                )
                or exec_description
            )

            exec_keywords = (
                Prompt.ask(
                    ':grey_question: Please give some [bold]keywords[/bold] to help people search your executor [dim](separated by space)[/dim]\n'
                    f'[dim]Example: image cv embedding encoding resnet[/dim]'
                )
                or exec_keywords
            )

            exec_url = (
                Prompt.ask(
                    ':grey_question: What is the [bold]URL[/bold] for GitHub repo?\n'
                    f'[dim]Example: https://github.com/yourname/my-executor[/dim]'
                )
                or exec_url
            )

            print(
                Panel.fit(
                    '''
[bold]Dockerfile[/bold] describes how this executor will be built. It is useful when 
your executor has non-trivial dependencies or must be run under certain environment. 

- If the [bold]Dockerfile[/bold] is missing, Jina automatically generates one for you. 
- If you provide one, then Jina will respect the given [bold]Dockerfile[/bold].''',
                    title='[Optional] [bold]Dockerfile[/bold]',
                    width=80,
                )
            )

            is_dockerfile = Confirm.ask(
                ':grey_question: Do you need to write your own [bold]Dockerfile[/bold] instead of the auto-generated one?',
                default=False,
            )

            print('[green]That\'s all we need to create an Executor![/green]')

        def mustache_repl(srcs):
            for src in track(
                srcs, description=f'Creating {exec_name}...', total=len(srcs)
            ):
                with open(
                    os.path.join(__resources_path__, 'executor-template', src)
                ) as fp, open(os.path.join(exec_path, src), 'w') as fpw:
                    f = (
                        fp.read()
                        .replace('{{exec_name}}', exec_name)
                        .replace('{{exec_description}}', exec_description)
                        .replace('{{exec_keywords}}', exec_keywords)
                        .replace('{{exec_url}}', exec_url)
                    )

                    f = [
                        v + '\n' for v in f.split('\n') if not ('{{' in v or '}}' in v)
                    ]
                    fpw.writelines(f)

        Path(exec_path).mkdir(parents=True, exist_ok=True)
        pkg_files = [
            'executor.py',
            'manifest.yml',
            'README.md',
            'requirements.txt',
            'config.yml',
        ]

        if is_dockerfile:
            pkg_files.append('Dockerfile')

        mustache_repl(pkg_files)

        table = Table(box=box.SIMPLE)
        table.add_column('Filename', style='cyan', no_wrap=True)
        table.add_column('Description', no_wrap=True)

        table.add_row('executor.py', 'The main logic file of the Executor.')
        table.add_row(
            'config.yml',
            'The YAML config file of the Executor. You can define [bold]__init__[/bold] arguments using [bold]with[/bold] keyword.',
        )
        table.add_row(
            '',
            Panel(
                Syntax(
                    f'''
jtype: {exec_name}
with:
    foo: 1
    bar: hello
py_modules:
    - executor.py
                ''',
                    'yaml',
                    theme='monokai',
                    line_numbers=True,
                    word_wrap=True,
                ),
                title='config.yml',
                width=50,
                expand=False,
            ),
        )
        table.add_row('README.md', 'The usage of the Executor.')
        table.add_row('requirements.txt', 'The Python dependencies of the Executor.')
        table.add_row(
            'manifest.yml',
            'The annotations of the Executor for getting better appealing on Jina Hub.',
        )

        field_table = Table(box=box.SIMPLE)
        field_table.add_column('Field', style='cyan', no_wrap=True)
        field_table.add_column('Description', no_wrap=True)
        field_table.add_row('name', 'Human-readable title of the Executor')
        field_table.add_row('alias', 'The unique identifier in Jina Hub')
        field_table.add_row('description', 'Human-readable description of the Executor')
        field_table.add_row('url', 'URL to find more information on the Executor')
        field_table.add_row('keywords', 'Keywords that help user find the Executor')

        table.add_row('', field_table)

        if is_dockerfile:
            table.add_row(
                'Dockerfile',
                'The Dockerfile describes how this executor will be built.',
            )

        final_table = Table(box=None)

        final_table.add_row(
            'Congrats! You have successfully created an Executor! Here are the next steps:'
        )

        p0 = Panel(
            Syntax(
                f'cd {exec_path}\nls',
                'console',
                theme='monokai',
                line_numbers=True,
                word_wrap=True,
            ),
            title='1. Checkout the Generated Executor',
            width=120,
            expand=False,
        )

        p1 = Panel(
            table,
            title='2. Understand Folder Structure',
            width=120,
            expand=False,
        )

        p2 = Panel(
            Syntax(
                f'jina hub push {exec_path}',
                'console',
                theme='monokai',
                line_numbers=True,
                word_wrap=True,
            ),
            title='3. Share it to Jina Hub',
            width=120,
            expand=False,
        )

        final_table.add_row(p0)
        final_table.add_row(p1)
        final_table.add_row(p2)

        p = Panel(
            final_table,
            title=':tada: Next Steps',
            width=130,
            expand=False,
        )
        console.print(p)

    def push(self) -> None:
        """Push the executor pacakge to Jina Hub."""

        from rich.console import Console

        work_path = Path(self.args.path)

        exec_tags = None
        if self.args.tag:
            exec_tags = ','.join(self.args.tag)

        dockerfile = None
        if self.args.docker_file:
            dockerfile = Path(self.args.docker_file)
            if not dockerfile.exists():
                raise Exception(f'The given Dockerfile `{dockerfile}` does not exist!')
            if dockerfile.parent != work_path:
                raise Exception(
                    f'The Dockerfile must be placed at the given folder `{work_path}`'
                )

            dockerfile = dockerfile.relative_to(work_path)

        console = Console()
        with console.status(f'Pushing `{self.args.path}` ...') as st:
            req_header = self._get_request_header()
            try:
                st.update(f'Packaging {self.args.path} ...')
                md5_hash = hashlib.md5()
                bytesio = archive_package(work_path)
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

                if exec_tags:
                    form_data['tags'] = exec_tags

                if dockerfile:
                    form_data['dockerfile'] = str(dockerfile)

                uuid8, secret = load_secret(work_path)
                if self.args.force or uuid8:
                    form_data['force'] = self.args.force or uuid8
                if self.args.secret or secret:
                    form_data['secret'] = self.args.secret or secret

                method = 'put' if ('force' in form_data) else 'post'

                st.update(f'Connecting Hubble ...')
                hubble_url = get_hubble_url()

                # upload the archived executor to Jina Hub
                st.update(f'Uploading ...')
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
                        console.print(f'=> {stream_msg["stream"]}')
                    elif 'status' in stream_msg:
                        st.update(f'{stream_msg["status"]}')
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
                        dump_secret(work_path, new_uuid8, new_secret)
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
    @disk_cache_offline(cache_file=str(_cache_file))
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
            uuid=resp['id'],
            alias=resp.get('alias', None),
            sn=resp.get('sn', None),
            tag=resp['tag'],
            visibility=resp['visibility'],
            image_name=resp['image'],
            archive_url=resp['package']['download'],
            md5sum=resp['package']['md5'],
        )

    def _pull_with_progress(self, log_streams, console):
        from rich.progress import Progress, DownloadColumn, BarColumn

        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            DownloadColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            console=console,
            transient=True,
        ) as progress:
            tasks = {}
            for log in log_streams:
                if 'status' not in log:
                    continue
                status = log['status']
                status_id = log.get('id', None)
                pg_detail = log.get('progressDetail', None)

                if (pg_detail is None) or (status_id is None):
                    console.print(status)
                    continue

                if status_id not in tasks:
                    tasks[status_id] = progress.add_task(status, total=0)

                task_id = tasks[status_id]

                if ('current' in pg_detail) and ('total' in pg_detail):
                    progress.update(
                        task_id,
                        completed=pg_detail['current'],
                        total=pg_detail['total'],
                        description=status,
                    )
                elif not pg_detail:
                    progress.update(task_id, advance=0, description=status)

    def pull(self) -> str:
        """Pull the executor package from Jina Hub.

        :return: the `uses` string
        """
        from rich.console import Console

        console = Console()
        cached_zip_file = None
        usage = None

        try:
            with console.status(f'Pulling {self.args.uri}...') as st:
                scheme, name, tag, secret = parse_hub_uri(self.args.uri)

                st.update(f'Fetching meta data of {name}...')
                executor = HubIO._fetch_meta(name, tag=tag, secret=secret)
                usage = (
                    f'{executor.uuid}'
                    if executor.visibility == 'public'
                    else f'{executor.uuid}:{secret}'
                )

            if scheme == 'jinahub+docker':
                self._load_docker_client()
                self._pull_with_progress(
                    self._raw_client.pull(
                        executor.image_name, stream=True, decode=True
                    ),
                    console,
                )

                return f'docker://{executor.image_name}'
            elif scheme == 'jinahub':
                import filelock

                with filelock.FileLock(get_lockfile(), timeout=-1):
                    try:
                        pkg_path, pkg_dist_path = resolve_local(executor)
                        # check serial number to upgrade
                        sn_file_path = pkg_dist_path / f'PKG-SN-{executor.sn or 0}'
                        if (not sn_file_path.exists()) and any(
                            pkg_dist_path.glob('PKG-SN-*')
                        ):
                            raise FileNotFoundError(f'{pkg_path} need to be upgraded')
                        if self.args.install_requirements:
                            requirements_file = pkg_dist_path / 'requirements.txt'
                            if requirements_file.exists():
                                install_requirements(requirements_file)
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

                    with console.status(f'Downloading {name} ...') as st:
                        cached_zip_file = download_with_resume(
                            executor.archive_url,
                            cache_dir,
                            f'{executor.uuid}-{executor.md5sum}.zip',
                            md5sum=executor.md5sum,
                        )

                        st.update(f'Unpacking {name} ...')
                        install_local(
                            cached_zip_file,
                            executor,
                            install_deps=self.args.install_requirements,
                        )

                        pkg_path, _ = resolve_local(executor)
                    return f'{pkg_path / "config.yml"}'
            else:
                raise ValueError(f'{self.args.uri} is not a valid scheme')
        except Exception as e:
            self.logger.error(f'Error while pulling {self.args.uri}: \n{e!r}')
            raise e
        finally:
            # delete downloaded zip package if existed
            if cached_zip_file is not None:
                cached_zip_file.unlink()

            if not self.args.no_usage and usage:
                self._get_prettyprint_usage(console, usage)
