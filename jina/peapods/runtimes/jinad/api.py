import asyncio
import json
from contextlib import ExitStack
from pathlib import Path
from typing import Dict, Tuple, Set, List, Optional

from ....jaml.helper import complete_path
from ....enums import RemotePeapodType
from ....importer import ImportExtensions
from ....jaml import JAML
from ....logging import JinaLogger


def _add_file_to_list(_file: str, _file_list: Set, logger: 'JinaLogger'):
    if _file and _file.endswith(('yml', 'yaml', 'py')):
        real_file = complete_path(_file)
        if Path(real_file).is_file():
            _file_list.add(real_file)
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
                result = JAML.load_no_tags(f)

            if 'metas' in result and 'py_modules' in result['metas']:
                _add_file_to_list(_file=result['metas']['py_modules'],
                                  _file_list=pymodules_files,
                                  logger=logger)

    return uses_files, pymodules_files


class JinadAPI:
    kind = 'pea'  # select from pea/pod, TODO: enum
    TIMEOUT_ERROR_CODE = 4000

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
        if self.kind not in ('pea', 'pod'):
            raise ValueError(f'kind must be pea/pod')

        # for now it is http. but it can be https or unix socket or fd
        # TODO: for https, the jinad server would need a tls certificate.
        # no changes would be required in terms of how the api gets invoked,
        # as requests does ssl verfication. we'd need to add some exception handling logic though
        base_url = f'{host}:{port}'
        rest_url = f'http://{base_url}'
        websocket_url = f'ws://{base_url}'
        self.alive_url = f'{rest_url}/alive'
        self.upload_url = f'{rest_url}/upload'
        self.pea_url = f'{rest_url}/pea'
        self.pod_url = f'{rest_url}/pod'
        self.log_url = f'{websocket_url}/logstream'

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
                self.logger.error(f'something wrong on remote: {ex!r}')

    def create(self, args: Dict, **kwargs) -> Optional[str]:
        """ Create a remote pea/pod
        :param args: the arguments in dict that pea can accept.
                     (convert argparse.Namespace to Dict before passing to this method)
        :return: the identity of the spawned pea/pod
        """
        with ImportExtensions(required=True):
            import requests

        try:
            url = self.pea_url if self.kind == 'pea' else self.pod_url
            r = requests.put(url=url, json=args, timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                return r.json()[f'{self.kind}_id']
            self.logger.error(f'couldn\'t create pod with remote jinad {r.json()}')
        except requests.exceptions.RequestException as ex:
            self.logger.error(f'couldn\'t create pod with remote jinad {ex!r}')

    async def logstream(self, remote_id: 'str', log_id: 'str'):
        """ websocket log stream from remote pea/pod
        :param remote_id: the identity of that pea/pod
        :return:
        """
        with ImportExtensions(required=True):
            import websockets

        self.logger.info(f'🌏 Fetching streamed logs from remote id: {remote_id}')
        remote_loggers = {}
        try:
            # sleeping for few seconds to allow the logs to be written in remote
            await asyncio.sleep(3)

            async with websockets.connect(f'{self.log_url}/{remote_id}?timeout=5') as websocket:
                current_line_number = -1

                while True:
                    await websocket.send(json.dumps({'from': int(current_line_number) + 1}))
                    async for log_line in websocket:
                        try:
                            log_line = json.loads(log_line)
                            if 'code' in log_line and log_line['code'] == self.TIMEOUT_ERROR_CODE:
                                self.logger.info(f'Received timeout from the log server. Breaking')
                                break
                            current_line_number = list(log_line.keys())[0]
                            complete_log_message = log_line[current_line_number]
                            log_line_dict = json.loads(complete_log_message.split('\t')[-1].strip())
                            name = log_line_dict['name']

                            if name not in remote_loggers:
                                remote_loggers[name] = JinaLogger(context=f'🌏 {name}', log_id=log_id)

                            # TODO(Deepankar): change logging level, process name in local logger
                            remote_loggers[name].info(f'{log_line_dict["message"].strip()}')
                        except json.decoder.JSONDecodeError:
                            continue
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.error(f'🌏 Client got disconnected from server')
        except websockets.exceptions.WebSocketException as e:
            self.logger.error(f'🌏 Got following error while streaming logs via websocket {e!r}')
        except asyncio.CancelledError:
            self.logger.info(f'🌏 Logging task cancelled successfully')
        finally:
            self.logger.info(f'🌏 Exiting from remote loggers')
            if remote_loggers:
                for logger in remote_loggers.values():
                    logger.close()

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
