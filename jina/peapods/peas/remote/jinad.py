import asyncio
import json
from contextlib import ExitStack
from multiprocessing.synchronize import Event
from pathlib import Path
from typing import Dict, Tuple, Set, List, Optional

import ruamel.yaml

from ....excepts import RemotePodClosed
from ....importer import ImportExtensions
from ....logging import JinaLogger


def _add_file_to_list(_file: str, _file_list: Set, logger: 'JinaLogger'):
    if _file and _file.endswith(('yml', 'yaml', 'py')):
        if Path(_file).is_file():
            _file_list.add(_file)
            logger.debug(f'adding file {_file} to be uploaded to remote context')
        else:
            logger.warning(f'file {_file} doesn\'t exist in the disk')


def _add_files_in_main_yaml(current_pea: Dict, uses_files: Set, pymodules_files: Set, logger: 'JinaLogger'):
    for _arg in ['uses', 'uses_before', 'uses_after']:
        if _arg in current_pea:
            _add_file_to_list(_file=current_pea.get(_arg),
                              _file_list=uses_files,
                              logger=logger)

    _add_file_to_list(_file=current_pea.get('py_modules'),
                      _file_list=pymodules_files,
                      logger=logger)


def fetch_files_from_yaml(pea_args: Dict, logger: 'JinaLogger') -> Tuple[Set[str], Set[str]]:
    """ helper function to fetch yaml & pymodules to be uploaded to remote """
    uses_files = set()
    pymodules_files = set()

    _pea_list = []
    if 'peas' in pea_args:
        # This is for remote Pods
        if isinstance(pea_args['peas'], list):
            for _pea_args in pea_args['peas']:
                _pea_list.append(_pea_args)
    else:
        # This is for remote Peas
        _pea_list.append(pea_args)

    for _pea_args in _pea_list:
        _add_files_in_main_yaml(current_pea=_pea_args,
                                uses_files=uses_files,
                                pymodules_files=pymodules_files,
                                logger=logger)

    if uses_files:
        for current_file in uses_files:
            with open(current_file) as f:
                result = ruamel.yaml.round_trip_load(f)

            if 'metas' in result and 'py_modules' in result['metas']:
                _add_file_to_list(_file=result['metas']['py_modules'],
                                  _file_list=pymodules_files,
                                  logger=logger)

    return uses_files, pymodules_files


class JinadAPI:
    kind = 'pea'  # select from pea/pod, TODO: enum

    def __init__(self,
                 host: str,
                 port: int,
                 version: str = 'v1',
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
        if self.kind not in ('pea', 'pod'):
            raise ValueError(f'kind must be pea/pod')

        # for now it is http. but it can be https or unix socket or fd
        # TODO: for https, the jinad server would need a tls certificate.
        # no changes would be required in terms of how the api gets invoked,
        # as requests does ssl verfication. we'd need to add some exception handling logic though
        url = f'{host}:{port}/{version}'
        rest_url = f'http://{url}'
        websocket_url = f'ws://{url}'
        self.alive_url = f'{rest_url}/alive'
        self.upload_url = f'{rest_url}/upload'
        self.pea_url = f'{rest_url}/pea'
        self.pod_url = f'{rest_url}/pod'
        self.log_url = f'{websocket_url}/wslog'

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
            self.logger.error(f'something wrong on remote: {repr(ex)}')
            return False

    def upload(self, args: Dict, **kwargs) -> bool:
        """ Upload local file dependencies to remote server by extracting from the pea_args

        :param args: the arguments in dict that pea can accept
        :return: if upload is successful
        """
        import requests

        uses_files, pymodules_files = fetch_files_from_yaml(pea_args=args, logger=self.logger)

        with ExitStack() as file_stack:
            files = []  # type: List[Tuple[str, bytes]]

            if uses_files:
                files.extend([('uses_files', file_stack.enter_context(open(fname, 'rb')))
                              for fname in uses_files])
            if pymodules_files:
                files.extend([('pymodules_files', file_stack.enter_context(open(fname, 'rb')))
                              for fname in pymodules_files])
            if not files:
                self.logger.debug('no files to be uploaded to remote')
                return True
            try:
                r = requests.put(url=self.upload_url, files=files, timeout=self.timeout)
                if r.status_code == requests.codes.ok:
                    self.logger.success(f'Got status {r.json()["status"]} from remote')
                    return True
            except requests.exceptions.RequestException as ex:
                self.logger.error(f'something wrong on remote: {repr(ex)}')

    def create(self, args: Dict, pod_type: str = 'flow', **kwargs) -> Optional[str]:
        """ Create a remote pea/pod

        :param args: the arguments in dict that pea can accept
        :param pod_type: two types of pod, can be ``cli``, ``flow`` TODO: need clarify this
        :return: the identity of the spawned pea/pod
        """
        with ImportExtensions(required=True):
            import requests

        try:
            url = self.pea_url if self.kind == 'pea' else f'{self.pod_url}/{pod_type}'
            r = requests.put(url=url, json=args, timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                return r.json()[f'{self.kind}_id']
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'couldn\'t create {pod_type} with remote jinad {repr(ex)}')

    async def wslogs(self, remote_id: 'str', stop_event: Event, current_line: int = 0):
        """ websocket log stream from remote pea/pod

        :param remote_id: the identity of that pea/pod
        :param stop_event: the multiprocessing event which marks if stop event is set
        :param current_line: the line number from which logs would be streamed
        :return:
        """
        with ImportExtensions(required=True):
            import websockets

        try:
            # sleeping for few seconds to allow the logs to be written in remote
            await asyncio.sleep(3)
            async with websockets.connect(f'{self.log_url}/{remote_id}?timeout=20') as websocket:
                await websocket.send(json.dumps({'from': current_line}))
                remote_loggers = {}
                while True:
                    log_line = await websocket.recv()
                    if log_line:
                        try:
                            log_line = json.loads(log_line)
                            current_line = int(list(log_line.keys())[0])
                            log_line_dict = list(log_line.values())[0]
                            log_line_dict = json.loads(log_line_dict.split('\t')[-1].strip())
                            name = log_line_dict['name']
                            if name not in remote_loggers:
                                remote_loggers[name] = JinaLogger(context=f'🌏 {name}')
                            # TODO: change logging level, process name in local logger
                            remote_loggers[name].info(f'{log_line_dict["message"].strip()}')
                        except json.decoder.JSONDecodeError:
                            continue
                    await websocket.send(json.dumps({}))
                    if stop_event.is_set():
                        for logger in remote_loggers.values():
                            logger.close()
                        raise RemotePodClosed
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.debug(f'Client got disconnected from server')
            return current_line
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(f'Got following error while streaming logs via websocket {repr(e)}')
            return 0

    def log(self, remote_id: 'str', stop_event: Event, **kwargs) -> None:
        """ Start the log stream from remote pea/pod, will use local logger for output

        :param remote_id: the identity of that pea/pod
        :return:
        """
        current_line = 0
        try:
            self.logger.info(f'fetching streamed logs from remote id: {remote_id}')
            while True:
                current_line = asyncio.run(self.wslogs(
                    remote_id=remote_id, stop_event=stop_event, current_line=current_line))
        except RemotePodClosed:
            self.logger.debug(f'🌏 remote closed')
        finally:
            self.logger.info(f'🌏 exiting from remote logger')

    def delete(self, remote_id: 'str', **kwargs) -> bool:
        """ Delete a remote pea/pod

        :param kind: pea/pod
        :param remote_id: the identity of that pea/pod
        :return: True if the deletion is successful
        """
        with ImportExtensions(required=True):
            import requests

        try:
            url = f'{self.pea_url}/?pea_id={remote_id}' if self.kind == 'pea' else f'{self.pod_url}/?pod_id={remote_id}'
            r = requests.delete(url=url, timeout=self.timeout)
            return r.status_code == requests.codes.ok
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'couldn\'t connect with remote jinad url {repr(ex)}')
            return False


class PeaAPI(JinadAPI):
    """Pea API, we might have different endpoints for peas & pods later"""
    kind = 'pea'


class PodAPI(JinadAPI):
    """Pod API, we might have different endpoints for peas & pods later"""
    kind = 'pod'
