import uuid
from pathlib import Path
from typing import Dict, Tuple, Set
from contextlib import ExitStack

import ruamel.yaml

from jina.helper import colored


def _add_file_to_list(_file: str, _file_list: Set, logger):
    if _file and _file.endswith(('yml', 'yaml', 'py')):
        if Path(_file).is_file():
            _file_list.add(_file)
            logger.debug(f'adding file {_file} to be uploaded to remote context')
        else:
            logger.warning(f'file {_file} doesn\'t exist in the disk')


def _add_files_in_main_yaml(current_pea: Dict, uses_files: Set, pymodules_files: Set, logger):
    for _arg in ['uses', 'uses_before', 'uses_after']:
        if _arg in current_pea:
            _add_file_to_list(_file=current_pea.get(_arg),
                              _file_list=uses_files,
                              logger=logger)

    _add_file_to_list(_file=current_pea.get('py_modules'),
                      _file_list=pymodules_files,
                      logger=logger)


def fetch_files_from_yaml(pea_args: Dict, logger) -> Tuple[set, set]:
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
    def __init__(self,
                 host: str,
                 port: int,
                 logger):
        self.logger = logger
        self.base_url = f'http://{host}:{port}/v1'
        self.alive_url = f'{self.base_url}/alive'
        self.upload_url = f'{self.base_url}/upload'
        self.pea_url = f'{self.base_url}/pea'
        self.pod_url = f'{self.base_url}/pod'
        self.log_url = f'{self.base_url}/log'

        try:
            import requests
        except (ImportError, ModuleNotFoundError):
            self.logger.critical('missing "requests" dependency, please do pip install "jina[http]"'
                                 'to enable remote Pea/Pod invocation')

    def is_alive(self):
        import requests
        try:
            r = requests.get(url=self.alive_url)
            return True if r.status_code == requests.codes.ok else False
        except requests.exceptions.ConnectionError:
            return False

    def _upload_files(self, uses_files, pymodules_files):
        import requests

        with ExitStack() as file_stack:
            files = []
            if uses_files:
                files.extend([('uses_files', file_stack.enter_context(open(fname, 'rb')))
                              for fname in uses_files])
            if pymodules_files:
                files.extend([('pymodules_files', file_stack.enter_context(open(fname, 'rb')))
                              for fname in pymodules_files])
            if not files:
                self.logger.info('nothing to upload to remote')
                return

            r = requests.put(url=self.upload_url,
                             files=files)
            if r.status_code == requests.codes.ok:
                self.logger.info(f'Got status {colored(r.json()["status"], "green")} from remote')

    def create(self, kind: str, pea_args: Dict, pod_type: str = 'flow'):
        import requests
        try:
            url = self.pea_url if kind == 'pea' else f'{self.pod_url}/{pod_type}'
            r = requests.put(url=url,
                             json=pea_args)
            return r.json()[f'{kind}_id'] if r.status_code == requests.codes.ok else None
        except requests.exceptions.ConnectionError:
            self.logger.error('couldn\'t connect with remote jinad url')
            return None

    def log(self, kind: str, remote_id: uuid.UUID):
        import requests
        try:
            if kind not in ('pea', 'pod'):
                return
            url = f'{self.log_url}/?{kind}_id={remote_id}'
            r = requests.get(url=url,
                             stream=True)
            for log_line in r.iter_content():
                if log_line:
                    self.logger.info(f'🌏 {log_line}')
        except requests.exceptions.ConnectionError:
            self.logger.error('couldn\'t connect with remote jinad url')
        finally:
            return self.logger.info(f'🌏 exiting from remote logger')

    def delete(self, kind: str, remote_id: uuid.UUID):
        import requests
        try:
            url = f'{self.pea_url}/?pea_id={remote_id}' if kind == 'pea' else f'{self.pod_url}/?pod_id={remote_id}'
            r = requests.delete(url=url)
            return r.status_code == requests.codes.ok
        except requests.exceptions.ConnectionError:
            self.logger.error('couldn\'t connect with remote jinad url')
            return False


class PeaAPI(JinadAPI):
    def __init__(self, host: str, port: int, logger):
        super().__init__(host=host, port=port, logger=logger)

    def upload(self, pea_args):
        try:
            _uses_files, _pymodules_files = fetch_files_from_yaml(pea_args=pea_args,
                                                                  logger=self.logger)
            self._upload_files(uses_files=_uses_files,
                               pymodules_files=_pymodules_files)
        except Exception as e:
            self.logger.error(f'got an error while uploading context files to remote pea {repr(e)}')

    def create(self, pea_args: Dict):
        return super().create(kind='pea', pea_args=pea_args)

    def log(self, pea_id: uuid.UUID):
        super().log(kind='pea', remote_id=pea_id)

    def delete(self, pea_id: uuid.UUID):
        return super().delete(kind='pea', remote_id=pea_id)


class PodAPI(JinadAPI):
    def __init__(self, host: str, port: int, logger):
        super().__init__(host=host, port=port, logger=logger)

    def upload(self, pea_args: Dict):
        try:
            _uses_files, _pymodules_files = fetch_files_from_yaml(pea_args=pea_args,
                                                                  logger=self.logger)
            self._upload_files(uses_files=_uses_files,
                               pymodules_files=_pymodules_files)
        except Exception as e:
            self.logger.error(f'got an error while uploading context files to remote pod {repr(e)}')

    def create(self, pea_args: Dict, pod_type: str = 'flow'):
        return super().create(kind='pod', pea_args=pea_args, pod_type=pod_type)

    def log(self, pod_id: uuid.UUID):
        super().log(kind='pod', remote_id=pod_id)

    def delete(self, pod_id: uuid.UUID):
        return super().delete(kind='pod', remote_id=pod_id)
