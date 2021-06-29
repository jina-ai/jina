import argparse
import asyncio
import copy
import json
import os
from argparse import Namespace
from contextlib import ExitStack
from typing import Optional, Sequence, Dict

from .... import __resources_path__
from ....enums import replace_enum_to_str
from ....importer import ImportExtensions
from ....jaml.helper import complete_path
from ....logging.logger import JinaLogger


class DaemonClient:
    """
    Jina Daemon client.

    :param host: the host address of ``jinad`` instance
    :param port: the port number of ``jinad`` instance
    :param logger: Jinalogger to log information.
    :param timeout: stop waiting for a response after a given number of seconds with the timeout parameter.
    """

    kind = 'pea'  # select from pea/pod, TODO: enum

    def __init__(
        self,
        host: str,
        port: int,
        logger: 'JinaLogger' = None,
        timeout: int = None,
        **kwargs,
    ):
        self.logger = logger or JinaLogger(host)
        self.timeout = timeout
        base_url = f'{host}:{port}'
        rest_url = f'http://{base_url}'
        self.alive_api = f'{rest_url}/'
        if self.kind not in ['pea', 'pod', 'workspace']:
            raise ValueError(f'daemon kind {self.kind} is not supported')
        self.store_api = f'{rest_url}/{self.kind}s'
        self.logstream_api = f'ws://{base_url}/logstream'

    @property
    def alive(self) -> bool:
        """
        Return True if ``jinad`` is alive at remote

        :return: True if ``jinad`` is alive at remote else false
        """
        with ImportExtensions(required=True):
            import requests

        try:
            r = requests.get(url=self.alive_api, timeout=self.timeout)
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'remote manager is not alive: {ex!r}')
            return False

    def get(self, identity: str) -> Dict:
        """
        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    def post(self, *args, **kwargs) -> Dict:
        """
        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    def delete(self, *args, **kwargs) -> str:
        """
        # noqa: DAR101
        # noqa: DAR102
        """
        raise NotImplementedError

    def _daemonize_id(self, id: str, kind: str = 'workspace') -> str:
        return f'j{kind}-{id}'

    async def logstream(self, id: str):
        """Websocket log stream from remote Pea / Pod

        :param id:  the identity of that Pea / Pod
        """
        with ImportExtensions(required=True):
            import websockets

        remote_log_config = os.path.join(__resources_path__, 'logging.remote.yml')
        all_remote_loggers = {}
        try:
            url = f'{self.logstream_api}/{id}'
            async with websockets.connect(url) as websocket:
                async for log_line in websocket:
                    try:
                        ll = json.loads(log_line)
                        name = ll['name']
                        if name not in all_remote_loggers:
                            all_remote_loggers[name] = JinaLogger(
                                context=ll['host'], log_config=remote_log_config
                            )

                        all_remote_loggers[name].info(
                            '{host} {name} {type} {message}'.format_map(ll)
                        )
                    except json.decoder.JSONDecodeError:
                        continue
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.warning(f'log streaming is disconnected')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(
                f'log streaming is disabled, you won\'t see logs on the remote\n Reason: {e!r}'
            )
        except asyncio.CancelledError:
            self.logger.warning(f'log streaming is cancelled')
        finally:
            for l in all_remote_loggers.values():
                l.close()

    def _mask_args(self, args: 'argparse.Namespace'):
        _args = copy.deepcopy(args)

        # reset the runtime to ZEDRuntime or ContainerRuntime
        if _args.runtime_cls == 'JinadRuntime':
            # TODO: add jinahub:// and jinahub+docker:// scheme here
            if _args.uses.startswith('docker://'):
                _args.runtime_cls = 'ContainerRuntime'
            else:
                _args.runtime_cls = 'ZEDRuntime'

        # TODO:/NOTE this prevents jumping from remote to another remote (Han: 2021.1.17)
        # _args.host = __default_host__
        # host resetting disables dynamic routing. Use `disable_remote` instead
        _args.disable_remote = True

        # NOTE: on remote relative filepaths should be converted to filename only
        def basename(field):
            if field and not field.startswith('docker://'):
                try:
                    return os.path.basename(complete_path(field))
                except FileNotFoundError:
                    pass
            return field

        for f in ('uses', 'uses_after', 'uses_before', 'py_modules'):
            attr = getattr(_args, f, None)
            if not attr:
                continue
            setattr(_args, f, [basename(m) for m in attr]) if isinstance(
                attr, list
            ) else setattr(_args, f, basename(attr))

        _args.log_config = ''  # do not use local log_config
        _args.upload_files = []  # reset upload files
        _args.noblock_on_start = False  # wait until start success

        changes = []
        for k, v in vars(_args).items():
            if v != getattr(args, k):
                changes.append(f'{k:>30s}: {str(getattr(args, k)):30s} -> {str(v):30s}')
        if changes:
            changes = [
                'note the following arguments have been masked or altered for remote purpose:'
            ] + changes
            self.logger.warning('\n'.join(changes))

        return _args


class PeaDaemonClient(DaemonClient):
    """Pea API, we might have different endpoints for peas & pods later"""

    kind = 'pea'

    def get(self, id: str) -> Dict:
        """Get status of the remote Pea / Pod

        :param id: 'DaemonID' based identity for the Pea
        :raises: requests.exceptions.RequestException
        :return: json response of the remote Pea / Pod status
        :rtype: Dict
        """

        with ImportExtensions(required=True):
            import requests

        try:
            r = requests.get(
                url=f'{self.store_api}/{self._daemonize_id(id, self.kind)}',
                timeout=self.timeout,
            )
            if r.status_code == requests.codes.not_found:
                self.logger.warning(f'couldn\'t find {id} in remote {self.kind} store')
            return r.json()
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'can\'t get status of {self.kind}: {ex!r}')

    def post(self, args: 'Namespace') -> Optional[str]:
        """Create a remote Pea / Pod

        :param args: the arguments for remote Pea
        :type args: Namespace
        :raises: requests.exceptions.RequestException
        :return: the identity of the spawned Pea / Pod
        :rtype: Optional[str]
        """

        with ImportExtensions(required=True):
            import requests

        try:
            payload = replace_enum_to_str(vars(self._mask_args(args)))
            # set timeout to None if args.timeout_ready is -1 (wait forever)
            r = requests.post(
                url=self.store_api,
                params={'workspace_id': self._daemonize_id(id=args.workspace_id)},
                json=payload,
                timeout=args.timeout_ready if args.timeout_ready != -1 else None,
            )
            rj = r.json()
            if r.status_code == 201:
                return rj
            elif r.status_code == 400:
                # known internal error
                rj_body = '\n'.join(j for j in rj['body'])
                self.logger.error(f'{rj["detail"]}\n{rj_body}')
            elif r.status_code == 422:
                self.logger.error(
                    'your payload is not correct, please follow the error message and double check'
                )
            raise requests.exceptions.RequestException(rj)
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'failed to create as {ex!r}')

    def delete(self, id: str, **kwargs) -> bool:
        """
        Delete a remote pea/pod

        :param id: the identity of that pea/pod
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """
        with ImportExtensions(required=True):
            import requests

        try:
            r = requests.delete(url=f'{self.store_api}/{id}', timeout=self.timeout)
            rj = r.json()
            if r.status_code != requests.codes.ok:
                rj_body = '\n'.join(j for j in rj['body'])
                self.logger.error(
                    f'deletion for {id} failed: {rj["detail"]}\n{rj_body}'
                )
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'failed to delete {id} as {ex!r}')
            return False


class PodDaemonClient(PeaDaemonClient):
    """Pod API, we might have different endpoints for peas & pods later"""

    kind = 'pod'


class WorkspaceDaemonClient(PeaDaemonClient):
    """ Defines interaction with Daemon Workspace API  """

    kind = 'workspace'

    def post(self, dependencies: Sequence[str], workspace_id: str) -> Optional[Dict]:
        """Create a remote workspace (includes file upload, docker build on remote)

        :param dependencies: file dependencies
        :param workspace_id: Workspace to which the files will get uploaded
        :raises: requests.exceptions.RequestException
        :return: dict response for upload
        """
        with ImportExtensions(required=True):
            import requests

        with ExitStack() as file_stack:
            files = [
                (
                    'files',
                    file_stack.enter_context(open(complete_path(f), 'rb')),
                )
                for f in dependencies
            ]
            try:
                if files:
                    self.logger.info(f'uploading {len(files)} file(s): {dependencies}')
                r = requests.post(
                    url=self.store_api,
                    params={'id': self._daemonize_id(id=workspace_id)},
                    files=files if files else None,
                    timeout=self.timeout,
                )
                rj = r.json()
                if r.status_code == requests.codes.created:
                    return rj
                else:
                    raise requests.exceptions.RequestException(rj)
            except requests.exceptions.RequestException as ex:
                self.logger.error(f'fail to upload as {ex!r}')

    def delete(self, id: str, **kwargs) -> bool:
        """
        Delete a remote workspace

        :param id: the identity of that pea/pod/workspace
        :param kwargs: keyword arguments
        :return: True if the deletion is successful
        """
        with ImportExtensions(required=True):
            import requests

        try:
            # NOTE: This deletes the container, network by default & leaves the files as-is on remote.
            # TODO: do we parameterize it?
            r = requests.delete(
                url=f'{self.store_api}/{self._daemonize_id(id)}',
                params={'container': True, 'network': True, 'files': False},
                timeout=self.timeout,
            )
            rj = r.json()
            if r.status_code != requests.codes.ok:
                rj_body = ''.join(j for j in rj['body'])
                self.logger.error(
                    f'deletion for {id} failed: {rj["detail"]}\n{rj_body}'
                )
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'failed to delete {id} as {ex!r}')
            return False
