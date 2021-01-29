import argparse
import asyncio
import copy
import json
from argparse import Namespace
from contextlib import ExitStack
from typing import Optional, Sequence, Dict

from pkg_resources import resource_filename

from .... import __default_host__
from ....enums import replace_enum_to_str
from ....importer import ImportExtensions
from ....jaml.helper import complete_path
from ....logging import JinaLogger


class DaemonClient:
    kind = 'pea'  # select from pea/pod, TODO: enum

    def __init__(self,
                 host: str,
                 port: int,
                 logger: 'JinaLogger' = None,
                 timeout: int = 5, **kwargs):
        """
        :param host: the host address of ``jinad`` instance
        :param port: the port number of ``jinad`` instance
        :param timeout: stop waiting for a response after a given number of seconds with the timeout parameter.
        :param logger:
        """
        self.logger = logger or JinaLogger(host)
        self.timeout = timeout
        # for now it is http. but it can be https or unix socket or fd
        # TODO: for https, the jinad server would need a tls certificate.
        # no changes would be required in terms of how the api gets invoked,
        # as requests does ssl verfication. we'd need to add some exception handling logic though
        base_url = f'{host}:{port}'
        rest_url = f'http://{base_url}'
        self.alive_api = f'{rest_url}/'
        self.upload_api = f'{rest_url}/workspaces'
        self.upload_api_arg = 'files'  # this is defined in Daemon API upload interface
        if self.kind == 'pea':
            self.store_api = f'{rest_url}/peas'
        elif self.kind == 'pod':
            self.store_api = f'{rest_url}/pods'
        else:
            raise ValueError(f'{self.kind} is not supported')
        self.logstream_api = f'ws://{base_url}/logstream'

    @property
    def is_alive(self) -> bool:
        """ Return True if ``jinad`` is alive at remote
        :return:
        """
        with ImportExtensions(required=True):
            import requests

        try:
            r = requests.get(url=self.alive_api, timeout=self.timeout)
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'remote manager is not alive: {ex!r}')
            return False

    def get_status(self, identity: str) -> Dict:
        with ImportExtensions(required=True):
            import requests

        try:
            r = requests.get(url=f'{self.store_api}/{identity}', timeout=self.timeout)
            rj = r.json()
            if r.status_code == 200:
                return rj
            raise requests.exceptions.RequestException(rj)
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'can\'t get status of {self.kind}: {ex!r}')

    def upload(self, dependencies: Sequence[str], workspace_id: str = None) -> str:
        """ Upload local file dependencies to remote server by extracting from the pea_args
        :param args: the arguments in dict that pea can accept
        :return: the workspace id
        """
        import requests

        with ExitStack() as file_stack:
            files = [(self.upload_api_arg, file_stack.enter_context(open(complete_path(f), 'rb')))
                     for f in dependencies]

            if files:
                try:
                    self.logger.info(f'uploading {len(files)} file(s): {dependencies}')
                    r = requests.post(url=self.upload_api,
                                      files=files,
                                      data={'workspace_id': workspace_id} if workspace_id else None,
                                      timeout=self.timeout)
                    rj = r.json()
                    if r.status_code == 201:
                        return rj
                    else:
                        raise requests.exceptions.RequestException(rj)
                except requests.exceptions.RequestException as ex:
                    self.logger.error(f'fail to upload as {ex!r}')

    def create(self, args: 'Namespace') -> Optional[str]:
        """ Create a remote pea/pod
        :param args: the arguments in dict that pea can accept.
                     (convert argparse.Namespace to Dict before passing to this method)
        :return: the identity of the spawned pea/pod
        """
        with ImportExtensions(required=True):
            import requests

        try:
            payload = replace_enum_to_str(vars(self._mask_args(args)))
            r = requests.post(url=self.store_api, json=payload, timeout=self.timeout)
            rj = r.json()
            if r.status_code == 201:
                return rj
            elif r.status_code == 400:
                # known internal error
                rj_body = '\n'.join(j for j in rj['body'])
                self.logger.error(f'{rj["detail"]}\n{rj_body}')
            elif r.status_code == 422:
                self.logger.error('your payload is not correct, please follow the error message and double check')
            raise requests.exceptions.RequestException(rj)
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'fail to create as {ex!r}')

    async def logstream(self, workspace_id: str, log_id: str):
        """Websocket log stream from remote pea/pod

        :param workspace_id: the identity of the workspace
        :param log_id: the identity of that pea/pod
        :return:
        """
        with ImportExtensions(required=True):
            import websockets

        remote_log_config = resource_filename('jina', '/'.join(
            ('resources', 'logging.remote.yml')))
        all_remote_loggers = {}
        try:
            async with websockets.connect(f'{self.logstream_api}/{workspace_id}/{log_id}') as websocket:
                async for log_line in websocket:
                    try:
                        ll = json.loads(log_line)
                        name = ll['name']
                        if name not in all_remote_loggers:
                            all_remote_loggers[name] = JinaLogger(context=ll['host'],
                                                                  log_config=remote_log_config)

                        all_remote_loggers[name].info('{host} {name} {type} {message}'.format_map(ll))
                    except json.decoder.JSONDecodeError:
                        continue
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.warning(f'log streaming is disconnected')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(f'log streaming is disabled, you won\'t see logs on the remote\n Reason: {e!r}')
        except asyncio.CancelledError:
            self.logger.info(f'log streaming is cancelled')
        finally:
            for l in all_remote_loggers.values():
                l.close()

    def delete(self, remote_id: str, **kwargs) -> bool:
        """ Delete a remote pea/pod
        :param remote_id: the identity of that pea/pod
        :return: True if the deletion is successful
        """
        with ImportExtensions(required=True):
            import requests

        try:
            url = f'{self.store_api}/{remote_id}'
            r = requests.delete(url=url, timeout=self.timeout)
            return r.status_code == 200
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'fail to delete {remote_id} as {ex!r}')
            return False

    def _mask_args(self, args: 'argparse.Namespace'):
        _args = copy.deepcopy(args)

        # reset the runtime to ZEDRuntime or ContainerRuntime
        if _args.runtime_cls == 'JinadRuntime':
            if _args.uses.startswith('docker://'):
                _args.runtime_cls = 'ContainerRuntime'
            else:
                _args.runtime_cls = 'ZEDRuntime'

        # reset the host default host
        # TODO:/NOTE this prevents jumping from remote to another remote (Han: 2021.1.17)
        _args.host = __default_host__

        _args.log_config = ''  # do not use local log_config
        _args.upload_files = []  # reset upload files

        changes = []
        for k, v in vars(_args).items():
            if v != getattr(args, k):
                changes.append(f'{k:>30s}: {str(getattr(args, k)):30s} -> {str(v):30s}')
        if changes:
            changes = ['note the following arguments have been masked or altered for remote purpose:'] + changes
            self.logger.warning('\n'.join(changes))

        return _args


class PeaDaemonClient(DaemonClient):
    """Pea API, we might have different endpoints for peas & pods later"""
    kind = 'pea'


class PodDaemonClient(DaemonClient):
    """Pod API, we might have different endpoints for peas & pods later"""
    kind = 'pod'
