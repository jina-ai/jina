"""Module for wrapping Jina Hub API calls."""

import argparse
import copy
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, Optional, Union

from jina import __resources_path__, __version__
from jina.helper import (
    ArgNamespace,
    colored,
    get_request_header,
    get_rich_console,
    retry,
)
from jina.hubble import HubExecutor
from jina.hubble.helper import (
    archive_package,
    disk_cache_offline,
    download_with_resume,
    get_cache_db,
    get_download_cache_dir,
    get_hubble_url_v2,
    parse_hub_uri,
    upload_file,
)
from jina.hubble.hubapi import (
    dump_secret,
    get_dist_path_of_executor,
    get_lockfile,
    install_local,
    install_package_dependencies,
    load_secret,
)
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.parsers.hubble import set_hub_parser


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
            import cryptography
            import filelock
            import rich

            assert rich  #: prevent pycharm auto remove the above line
            assert cryptography
            assert filelock

    def new(self) -> None:
        """Create a new executor folder interactively."""

        from rich import box, print
        from rich.panel import Panel
        from rich.progress import track
        from rich.prompt import Confirm, Prompt
        from rich.syntax import Syntax
        from rich.table import Table

        console = get_rich_console()

        print(
            Panel.fit(
                '''
[bold green]Executor[/bold green] is how Jina processes [bold]Document[/bold].

This guide helps you to create your own Executor in 30 seconds.''',
                title='Create New Executor',
            )
        )

        exec_name = (
            self.args.name
            if self.args.name
            else Prompt.ask(
                ':grey_question: What is the [bold]name[/bold] of your executor?\n'
                '[dim]CamelCase is required[/dim]',
                default=f'MyExecutor{random.randint(0, 100)}',
            )
        )

        exec_path = (
            self.args.path
            if self.args.path
            else Prompt.ask(
                ':grey_question: [bold]Which folder[/bold] to store your executor?',
                default=os.path.join(os.getcwd(), exec_name),
            )
        )
        exec_description = '{{}}'
        exec_keywords = '{{}}'
        exec_url = '{{}}'

        is_dockerfile = False

        if self.args.advance_configuration or Confirm.ask(
            '[green]That\'s all we need to create an Executor![/green]\n'
            ':grey_question: Or do you want to proceed to advanced configuration',
            default=False,
        ):
            exec_description = (
                self.args.description
                if self.args.description
                else (
                    Prompt.ask(
                        ':grey_question: Please give a [bold]short description[/bold] of your executor?\n'
                        f'[dim]Example: {exec_name} embeds images into 128-dim vectors using ResNet.[/dim]'
                    )
                )
            )

            exec_keywords = (
                self.args.keywords
                if self.args.keywords
                else (
                    Prompt.ask(
                        ':grey_question: Please give some [bold]keywords[/bold] to help people search your executor [dim](separated by comma)[/dim]\n'
                        f'[dim]Example: image cv embedding encoding resnet[/dim]'
                    )
                )
            )

            exec_url = (
                self.args.url
                if self.args.url
                else (
                    Prompt.ask(
                        ':grey_question: What is the [bold]URL[/bold] for GitHub repo?\n'
                        f'[dim]Example: https://github.com/yourname/my-executor[/dim]'
                    )
                )
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

            is_dockerfile = self.args.add_dockerfile or Confirm.ask(
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
                        .replace('{{exec_keywords}}', str(exec_keywords.split(',')))
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

        # adding the columns in order of `ls` output
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
metas:
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

        if is_dockerfile:
            table.add_row(
                'Dockerfile',
                'The Dockerfile describes how this executor will be built.',
            )

        table.add_row('executor.py', 'The main logic file of the Executor.')
        table.add_row(
            'manifest.yml',
            'Metadata for the Executor, for better appeal on Jina Hub.',
        )

        manifest_fields_table = Table(box=box.SIMPLE)
        manifest_fields_table.add_column('Field', style='cyan', no_wrap=True)
        manifest_fields_table.add_column('Description', no_wrap=True)
        manifest_fields_table.add_row('name', 'Human-readable title of the Executor')
        manifest_fields_table.add_row(
            'description', 'Human-readable description of the Executor'
        )
        manifest_fields_table.add_row(
            'url',
            'URL to find more information on the Executor (e.g. GitHub repo URL)',
        )
        manifest_fields_table.add_row(
            'keywords', 'Keywords that help user find the Executor'
        )

        table.add_row('', manifest_fields_table)
        table.add_row('README.md', 'A usage guide of the Executor.')
        table.add_row('requirements.txt', 'The Python dependencies of the Executor.')

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
            title='1. Check out the generated Executor',
            width=120,
            expand=False,
        )

        p1 = Panel(
            table,
            title='2. Understand folder structure',
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
            title=':tada: Next steps',
            width=130,
            expand=False,
        )
        console.print(p)

    def push(self) -> None:
        """Push the executor package to Jina Hub."""

        work_path = Path(self.args.path)

        exec_tags = None
        if self.args.tag:
            exec_tags = ','.join(self.args.tag)

        dockerfile = None
        if self.args.dockerfile:
            dockerfile = Path(self.args.dockerfile)
            if not dockerfile.exists():
                raise Exception(f'The given Dockerfile `{dockerfile}` does not exist!')
            if dockerfile.parent != work_path:
                raise Exception(
                    f'The Dockerfile must be placed at the given folder `{work_path}`'
                )

            dockerfile = dockerfile.relative_to(work_path)

        console = get_rich_console()
        with console.status(f'Pushing `{self.args.path}` ...') as st:
            req_header = get_request_header()
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

                if self.args.verbose:
                    form_data['verbose'] = 'True'

                if exec_tags:
                    form_data['tags'] = exec_tags

                if dockerfile:
                    form_data['dockerfile'] = str(dockerfile)

                uuid8, secret = load_secret(work_path)
                if self.args.force_update or uuid8:
                    form_data['id'] = self.args.force_update or uuid8
                if self.args.secret or secret:
                    form_data['secret'] = self.args.secret or secret

                st.update(f'Connecting to Jina Hub ...')
                if form_data.get('id') and form_data.get('secret'):
                    hubble_url = get_hubble_url_v2() + '/rpc/executor.update'
                else:
                    hubble_url = get_hubble_url_v2() + '/rpc/executor.create'

                # upload the archived executor to Jina Hub
                st.update(f'Uploading...')
                resp = upload_file(
                    hubble_url,
                    'filename',
                    content,
                    dict_data=form_data,
                    headers=req_header,
                    stream=True,
                    method='post',
                )

                image = None
                session_id = req_header.get('jinameta-session-id')
                for stream_line in resp.iter_lines():
                    stream_msg = json.loads(stream_line)

                    t = stream_msg.get('type')
                    subject = stream_msg.get('subject')
                    payload = stream_msg.get('payload', '')
                    if t == 'error':
                        msg = stream_msg.get('message')
                        if not msg and payload and isinstance(payload, dict):
                            msg = payload.get('readableMessage') or payload.get(
                                'message'
                            )

                        if 'Process(docker) exited on non-zero code' in msg:
                            self.logger.error(
                                '''
                            Failed on building Docker image. Potential solutions:
                            - If you haven't provide a Dockerfile in the executor bundle, you may want to provide one,
                              as the auto-generated one on the cloud did not work.
                            - If you have provided a Dockerfile, you may want to check the validity of this Dockerfile.
                            '''
                            )

                        raise Exception(
                            f'{msg or "Unknown Error"} session_id: {session_id}'
                        )
                    if t == 'progress' and subject == 'buildWorkspace':
                        legacy_message = stream_msg.get('legacyMessage', {})
                        status = legacy_message.get('status', '')
                        st.update(
                            f'Cloud building ... [dim]{subject}: {t} ({status})[/dim]'
                        )
                    elif t == 'complete':
                        image = stream_msg['payload']
                        st.update(
                            f'Cloud building ... [dim]{subject}: {t} ({stream_msg["message"]})[/dim]'
                        )
                        break
                    elif t and subject:
                        if self.args.verbose and t == 'console':
                            console.log(
                                f'Cloud building ... [dim]{subject}: {payload}[/dim]'
                            )
                        else:
                            st.update(
                                f'Cloud building ... [dim]{subject}: {t} {payload}[/dim]'
                            )

                if image:
                    new_uuid8, new_secret = self._prettyprint_result(console, image)
                    if new_uuid8 != uuid8 or new_secret != secret:
                        dump_secret(work_path, new_uuid8, new_secret)
                else:
                    raise Exception(f'Unknown Error, session_id: {session_id}')

            except KeyboardInterrupt:
                pass

            except Exception as e:  # IO related errors
                self.logger.error(
                    f'''Please report this session_id: {colored(req_header["jinameta-session-id"], color="yellow", attrs="bold")} to https://github.com/jina-ai/jina/issues'
                {e!r}'''
                )
                raise e

    def _prettyprint_result(self, console, image):
        # TODO: only support single executor now

        from rich.panel import Panel
        from rich.table import Table

        uuid8 = image['id']
        secret = image['secret']
        visibility = image['visibility']
        tag = self.args.tag[0] if self.args.tag else None

        table = Table.grid()
        table.add_column(width=20, no_wrap=True)
        table.add_column(style='cyan', no_wrap=True)
        table.add_row(
            ':link: Hub URL',
            f'[link=https://hub.jina.ai/executor/{uuid8}/]https://hub.jina.ai/executor/{uuid8}/[/link]',
        )
        if 'name' in image:
            table.add_row(':name_badge: Name', image['name'])
        table.add_row(':lock: Secret', secret)
        table.add_row(
            '',
            ':point_up:️ [bold red]Please keep this token in a safe place!',
        )
        table.add_row(':eyes: Visibility', visibility)

        p1 = Panel(
            table,
            title='Published',
            width=80,
            expand=False,
        )
        console.print(p1)

        presented_id = image.get('name', uuid8)
        usage = (
            f'{presented_id}' if visibility == 'public' else f'{presented_id}:{secret}'
        ) + (f'/{tag}' if tag else '')

        if not self.args.no_usage:
            self._get_prettyprint_usage(console, usage)

        return uuid8, secret

    def _get_prettyprint_usage(self, console, executor_name, usage_kind=None):
        from rich.panel import Panel
        from rich.syntax import Syntax

        flow_plain = f'''from jina import Flow

f = Flow().add(uses='jinahub://{executor_name}')
'''

        flow_docker = f'''from jina import Flow

f = Flow().add(uses='jinahub+docker://{executor_name}')
'''

        flow_sandbox = f'''from jina import Flow

f = Flow().add(uses='jinahub+sandbox://{executor_name}')
'''
        panels = [
            Panel(
                Syntax(
                    p[0],
                    'python',
                    theme='monokai',
                    word_wrap=True,
                ),
                title=p[1],
                width=80,
                expand=False,
            )
            for p in [
                (flow_plain, 'Use via source'),
                (flow_docker, 'Use in Docker'),
                (flow_sandbox, 'Use in Sandbox'),
            ]
        ]

        if usage_kind == 'docker':
            console.print(panels[1])
        elif usage_kind == 'source':
            console.print(panels[0])
        else:
            console.print(*reversed(panels))

    @staticmethod
    @disk_cache_offline(cache_file=str(get_cache_db()))
    def fetch_meta(
        name: str,
        tag: str,
        *,
        secret: Optional[str] = None,
        image_required: bool = True,
        rebuild_image: bool = True,
        force: bool = False,
    ) -> HubExecutor:
        """Fetch the executor meta info from Jina Hub.
        :param name: the UUID/Name of the executor
        :param tag: the tag of the executor if available, otherwise, use `None` as the value
        :param secret: the access secret of the executor
        :param image_required: it indicates whether a Docker image is required or not
        :param rebuild_image: it indicates whether Jina Hub need to rebuild image or not
        :param force: if set to True, access to fetch_meta will always pull latest Executor metas, otherwise, default
            to local cache
        :return: meta of executor

        .. note::
            The `name` and `tag` should be passed via ``args`` and `force` and `secret` as ``kwargs``, otherwise,
            cache does not work.
        """
        with ImportExtensions(required=True):
            import requests

        @retry(num_retry=3)
        def _send_request_with_retry(url, **kwargs):
            resp = requests.post(url, **kwargs)
            if resp.status_code != 200:
                if resp.text:
                    raise Exception(resp.text)
                resp.raise_for_status()

            return resp

        pull_url = get_hubble_url_v2() + f'/rpc/executor.getPackage'

        payload = {'id': name, 'include': ['code'], 'rebuildImage': rebuild_image}
        if image_required:
            payload['include'].append('docker')
        if secret:
            payload['secret'] = secret
        if tag:
            payload['tag'] = tag

        req_header = get_request_header()

        resp = _send_request_with_retry(pull_url, json=payload, headers=req_header)
        resp = resp.json()['data']

        images = resp['package'].get('containers', [])
        image_name = images[0] if images else None
        if image_required and not image_name:
            raise Exception(
                f'No image found for executor "{name}", '
                f'tag: {tag}, commit: {resp.get("commit", {}).get("id")}, '
                f'session_id: {req_header.get("jinameta-session-id")}'
            )

        return HubExecutor(
            uuid=resp['id'],
            name=resp.get('name', None),
            commit_id=resp['commit'].get('id'),
            tag=tag or resp['commit'].get('tags', [None])[0],
            visibility=resp['visibility'],
            image_name=image_name,
            archive_url=resp['package']['download'],
            md5sum=resp['package']['md5'],
        )

    @staticmethod
    def deploy_public_sandbox(args: Union[argparse.Namespace, Dict]) -> str:
        """
        Deploy a public sandbox to Jina Hub.
        :param args: arguments parsed from the CLI

        :return: the host and port of the sandbox
        """
        args_copy = copy.deepcopy(args)
        if not isinstance(args_copy, Dict):
            args_copy = vars(args_copy)

        scheme, name, tag, secret = parse_hub_uri(args_copy.pop('uses', ''))
        payload = {
            'name': name,
            'tag': tag if tag else 'latest',
            'jina': __version__,
            'args': args_copy,
        }

        import requests

        console = get_rich_console()

        host = None
        port = None

        json_response = requests.post(
            url=get_hubble_url_v2() + '/rpc/sandbox.get',
            json=payload,
            headers=get_request_header(),
        ).json()
        if json_response.get('code') == 200:
            host = json_response.get('data', {}).get('host', None)
            port = json_response.get('data', {}).get('port', None)
            livetime = json_response.get('data', {}).get('livetime', '15 mins')

        if host and port:
            console.log(f"A sandbox already exists, reusing it.")
            console.log(
                f"[bold green]This sandbox will be removed when there has been no traffic for {livetime}"
            )

            return host, port

        with console.status(
            f"[bold green]Deploying sandbox for [bold white]{name}[/bold white] since none exists..."
        ):
            try:
                json_response = requests.post(
                    url=get_hubble_url_v2() + '/rpc/sandbox.create',
                    json=payload,
                    headers=get_request_header(),
                ).json()

                data = json_response.get('data') or {}
                host = data.get('host', None)
                port = data.get('port', None)
                livetime = data.get('livetime', '15 mins')
                if not host or not port:
                    raise Exception(f'Failed to deploy sandbox: {json_response}')

                console.log(f"Deployment completed: {host}:{port}")
                console.log(
                    f"[bold green]This sandbox will be removed when no traffic during [bold white]{livetime}[/bold white]"
                )
            except:
                console.log("Deployment failed")
                raise

        return host, port

    def _pull_with_progress(self, log_streams, console):
        from rich.progress import BarColumn, DownloadColumn, Progress

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
                    self.logger.debug(status)
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

    def _load_docker_client(self):
        with ImportExtensions(required=True):
            import docker
            import docker.errors
            from docker import APIClient

            from jina import __windows__

            try:
                self._client = docker.from_env()
                # low-level client
                self._raw_client = APIClient(
                    base_url=docker.constants.DEFAULT_NPIPE
                    if __windows__
                    else docker.constants.DEFAULT_UNIX_SOCKET
                )
            except docker.errors.DockerException:
                self.logger.critical(
                    f'Docker daemon seems not running. Please run Docker daemon and try again.'
                )
                exit(1)

    def pull(self) -> str:
        """Pull the executor package from Jina Hub.

        :return: the `uses` string
        """

        console = get_rich_console()
        cached_zip_file = None
        executor_name = None
        usage_kind = None

        try:
            need_pull = self.args.force_update
            with console.status(f'Pulling {self.args.uri}...') as st:
                scheme, name, tag, secret = parse_hub_uri(self.args.uri)
                image_required = scheme == 'jinahub+docker'

                st.update(f'Fetching [bold]{name}[/bold] from Jina Hub ...')
                executor, from_cache = HubIO.fetch_meta(
                    name,
                    tag,
                    secret=secret,
                    image_required=image_required,
                    force=need_pull,
                )

                presented_id = getattr(executor, 'name', executor.uuid)
                executor_name = (
                    f'{presented_id}'
                    if executor.visibility == 'public'
                    else f'{presented_id}:{secret}'
                ) + (f'/{tag}' if tag else '')

                if scheme == 'jinahub+docker':
                    self._load_docker_client()
                    import docker

                    try:
                        self._client.images.get(executor.image_name)
                    except docker.errors.ImageNotFound:
                        need_pull = True

                    if need_pull:
                        st.update(f'Pulling image ...')
                        log_stream = self._raw_client.pull(
                            executor.image_name, stream=True, decode=True
                        )
                        st.stop()
                        self._pull_with_progress(
                            log_stream,
                            console,
                        )
                    usage_kind = 'docker'
                    return f'docker://{executor.image_name}'
                elif scheme == 'jinahub':
                    import filelock

                    with filelock.FileLock(get_lockfile(), timeout=-1):
                        try:
                            pkg_path, pkg_dist_path = get_dist_path_of_executor(
                                executor
                            )
                            # check commit id to upgrade
                            commit_file_path = (
                                pkg_dist_path / f'PKG-COMMIT-{executor.commit_id or 0}'
                            )
                            if (not commit_file_path.exists()) and any(
                                pkg_dist_path.glob('PKG-COMMIT-*')
                            ):
                                raise FileNotFoundError(
                                    f'{pkg_path} need to be upgraded'
                                )

                            st.update('Installing [bold]requirements.txt[/bold]...')
                            install_package_dependencies(
                                install_deps=self.args.install_requirements,
                                pkg_dist_path=pkg_dist_path,
                                pkg_path=pkg_dist_path,
                            )

                        except FileNotFoundError:
                            need_pull = True

                        if need_pull:
                            # pull the latest executor meta, as the cached data would expire
                            if from_cache:
                                executor, _ = HubIO.fetch_meta(
                                    name,
                                    tag,
                                    secret=secret,
                                    image_required=False,
                                    force=True,
                                )

                            st.update(f'Downloading {name} ...')
                            cached_zip_file = download_with_resume(
                                executor.archive_url,
                                get_download_cache_dir(),
                                f'{executor.uuid}-{executor.md5sum}.zip',
                                md5sum=executor.md5sum,
                            )

                            st.update(f'Unpacking {name} ...')
                            install_local(
                                cached_zip_file,
                                executor,
                                install_deps=self.args.install_requirements,
                            )

                            pkg_path, _ = get_dist_path_of_executor(executor)

                        usage_kind = 'source'
                        return f'{pkg_path / "config.yml"}'
                else:
                    raise ValueError(f'{self.args.uri} is not a valid scheme')
        except KeyboardInterrupt:
            executor_name = None
        except Exception:
            executor_name = None
            raise
        finally:
            # delete downloaded zip package if existed
            if cached_zip_file is not None:
                cached_zip_file.unlink()

            if not self.args.no_usage and executor_name:
                self._get_prettyprint_usage(console, executor_name, usage_kind)
