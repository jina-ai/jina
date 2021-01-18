import asyncio
import json
import os
from argparse import Namespace
from contextlib import ExitStack
from typing import Tuple, List, Optional, Sequence

from ....enums import RemotePeapodType, replace_enum_to_str
from ....importer import ImportExtensions
from ....logging import JinaLogger


class JinadAPI:
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
        self.alive_url = f'{rest_url}/'
        self.upload_url = f'{rest_url}/upload'
        if self.kind == 'pea':
            self.peapod_url = f'{rest_url}/peas'
        elif self.kind == 'pod':
            self.peapod_url = f'{rest_url}/pods'
        else:
            raise ValueError(f'{self.kind} is not supported')
        self.log_url = f'ws://{base_url}/logstream'

    @property
    def is_alive(self) -> bool:
        """ Return True if ``jinad`` is alive at remote
        :return:
        """
        with ImportExtensions(required=True):
            import requests

        try:
            r = requests.get(url=self.alive_url, timeout=self.timeout)
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'something wrong on remote: {ex!r}')
            return False

    def upload(self, dependencies: Sequence[str]):
        """ Upload local file dependencies to remote server by extracting from the pea_args
        :param args: the arguments in dict that pea can accept
        :return: if upload is successful
        """
        import requests

        with ExitStack() as file_stack:
            files = [(os.path.basename(fname), file_stack.enter_context(open(fname, 'rb')))
                     for fname in dependencies]  # type: List[Tuple[str, bytes]]

            if files:
                try:
                    requests.post(url=self.upload_url, files=files, timeout=self.timeout)
                except requests.exceptions.RequestException as ex:
                    self.logger.error(f'something wrong on remote: {ex!r}')

    def create(self, args: 'Namespace', **kwargs) -> Optional[str]:
        """ Create a remote pea/pod
        :param args: the arguments in dict that pea can accept.
                     (convert argparse.Namespace to Dict before passing to this method)
        :return: the identity of the spawned pea/pod
        """
        with ImportExtensions(required=True):
            import requests

        try:
            payload = replace_enum_to_str(vars(args))
            r = requests.post(url=self.peapod_url, json={self.kind: payload}, timeout=self.timeout)
            if r.status_code == 201:
                return r.json()
            else:
                raise requests.exceptions.RequestException(r.json())
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'couldn\'t create on remote jinad: {ex!r}')

    async def logstream(self, remote_id: str):
        """ websocket log stream from remote pea/pod
        :param remote_id: the identity of that pea/pod
        :return:
        """
        with ImportExtensions(required=True):
            import websockets

        self.logger.info(f'Fetching streamed logs from remote id: {remote_id}')
        try:
            async with websockets.connect(f'{self.log_url}/{remote_id}') as websocket:
                async for log_line in websocket:
                    try:
                        ll = json.loads(log_line)
                        name = ll['name']
                        msg = ll['message'].strip()
                        self.logger.info(f'🌏 {name} {msg}')
                    except json.decoder.JSONDecodeError:
                        continue
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.error(f'Client got disconnected from server')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(f'Got following error while streaming logs via websocket {e!r}')
        except asyncio.CancelledError:
            self.logger.info(f'Logging task cancelled successfully')
        finally:
            self.logger.info(f'Exiting from remote loggers')

    def delete(self, remote_id: str, **kwargs) -> bool:
        """ Delete a remote pea/pod
        :param remote_id: the identity of that pea/pod
        :return: True if the deletion is successful
        """
        with ImportExtensions(required=True):
            import requests

        try:
            url = f'{self.peapod_url}/{remote_id}'
            r = requests.delete(url=url, timeout=self.timeout)
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'couldn\'t connect with remote jinad url {ex!r}')
            return False


class PeaJinadAPI(JinadAPI):
    """Pea API, we might have different endpoints for peas & pods later"""
    kind = 'pea'


class PodJinadAPI(JinadAPI):
    """Pod API, we might have different endpoints for peas & pods later"""
    kind = 'pod'


def get_jinad_api(kind: str, host: str, port: int, logger: JinaLogger, **kwargs):
    if kind == RemotePeapodType.PEA:
        return PeaJinadAPI(host=host, port=port, logger=logger, **kwargs)
    elif kind == RemotePeapodType.POD:
        return PodJinadAPI(host=host, port=port, logger=logger, **kwargs)
    else:
        raise ValueError(f'kind must be pea/pod but it is {kind}')
