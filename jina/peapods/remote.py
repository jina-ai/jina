__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from pathlib import Path
from argparse import Namespace
from contextlib import ExitStack
from typing import Callable, Dict, List, Tuple

import grpc
import ruamel.yaml

from .pea import BasePea
from ..helper import colored

from .zmq import Zmqlet, send_ctrl_message
from ..clients.python import GrpcClient
from ..helper import kwargs2list
from ..logging import JinaLogger
from ..proto import jina_pb2

if False:
    import argparse


class PeaSpawnHelper(GrpcClient):
    body_tag = 'pea'

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(args)
        self.args = args
        self.timeout_shutdown = 10
        self.callback_on_first = True
        self.args.log_remote = False
        self._remote_logger = JinaLogger('🌏', **vars(self.args))

    def call(self, set_ready: Callable = None):
        """
        :param set_ready: :func:`set_ready` signal from :meth:`jina.peapods.peas.BasePea.set_ready`
        :return:
        """
        req = jina_pb2.SpawnRequest()
        self.args.log_remote = True
        getattr(req, self.body_tag).args.extend(kwargs2list(vars(self.args)))
        self.remote_logging(req, set_ready)

    def remote_logging(self, req: 'jina_pb2.SpawnRequest', set_ready: Callable = None):
        try:
            for resp in self._stub.Spawn(req):
                if set_ready and self.callback_on_first:
                    set_ready(resp)
                    self.callback_on_first = False
                self._remote_logger.info(resp.log_record)
        except grpc.RpcError:
            pass

    def close(self):
        if not self.is_closed:
            if self.ctrl_addr:
                send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                                  timeout=self.timeout_shutdown)
            super().close()
            self.is_closed = True


class PodSpawnHelper(PeaSpawnHelper):
    body_tag = 'pod'

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.all_ctrl_addr = []  #: all peas control address and ports of this pod, need to be set in set_ready()

    def close(self):
        if not self.is_closed:
            for ctrl_addr in self.all_ctrl_addr:
                send_ctrl_message(ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                                  timeout=self.timeout_shutdown)
            GrpcClient.close(self)
            self.is_closed = True


class MutablePodSpawnHelper(PodSpawnHelper):

    def __init__(self, peas_args: Dict):
        inited = False
        for k in peas_args.values():
            if k:
                if not isinstance(k, list):
                    k = [k]
                if not inited:
                    # any pea will do, we just need its host and port_expose
                    super().__init__(k[0])
                    inited = True
                for kk in k:
                    kk.log_remote = True
                    self.all_ctrl_addr.append(Zmqlet.get_ctrl_address(kk)[0])
        self.args = peas_args

    def call(self, set_ready: Callable = None):

        self.remote_logging(peas_args2mutable_pod_req(self.args), set_ready)


def peas_args2mutable_pod_req(peas_args: Dict):
    def pod2pea_args_list(args):
        return kwargs2list(vars(args))

    req = jina_pb2.SpawnRequest()
    if peas_args['head']:
        req.mutable_pod.head.args.extend(pod2pea_args_list(peas_args['head']))
    if peas_args['tail']:
        req.mutable_pod.tail.args.extend(pod2pea_args_list(peas_args['tail']))
    if peas_args['peas']:
        for q in peas_args['peas']:
            _a = req.mutable_pod.peas.add()
            _a.args.extend(pod2pea_args_list(q))
    return req


def mutable_pod_req2peas_args(req):
    from ..parser import set_pea_parser
    return {
        'head': set_pea_parser().parse_known_args(req.head.args)[0] if req.head.args else None,
        'tail': set_pea_parser().parse_known_args(req.tail.args)[0] if req.tail.args else None,
        'peas': [set_pea_parser().parse_known_args(q.args)[0] for q in req.peas] if req.peas else []
    }


class RemotePea(BasePea):
    """A RemotePea that spawns a remote :class:`BasePea`
    Useful in Jina CLI
    """
    remote_helper = PeaSpawnHelper

    def loop_body(self):
        self._remote = self.remote_helper(self.args)
        self._remote.start(self.set_ready)  # auto-close after

    def close(self):
        self._remote.close()


class RemotePod(RemotePea):
    """A RemotePod that spawns a remote :class:`BasePod`
    Useful in Jina CLI
    """
    remote_helper = PodSpawnHelper

    def set_ready(self, resp):
        _rep = getattr(resp, resp.WhichOneof('body'))
        peas_args = mutable_pod_req2peas_args(_rep)
        all_args = peas_args['peas'] + (
            [peas_args['head']] if peas_args['head'] else []) + (
                       [peas_args['tail']] if peas_args['tail'] else [])
        for s in all_args:
            s.host = self.args.host
            self._remote.all_ctrl_addr.append(Zmqlet.get_ctrl_address(s)[0])
        super().set_ready()


def namespace_to_dict(args: Dict) -> Dict:
    """ helper function to convert argparse.Namespace to json to be uploaded via REST """
    pea_args = {}
    for k, v in args.items():
        if v is None:
            pea_args[k] = None
        if isinstance(v, Namespace):
            pea_args[k] = vars(v)
        if isinstance(v, list):
            pea_args[k] = []
            pea_args[k].extend([vars(_) for _ in v])
    return pea_args


def fetch_files_from_yaml(pea_args: Dict, logger) -> Tuple[set, set]:
    """ helper function to fetch yaml & pymodules to be uploaded to remote """
    def _file_adder(_file, _file_list):
        if _file and _file.endswith(('yml', 'yaml', 'py')):
            if Path(_file).is_file():
                _file_list.add(_file)
                logger.debug(f'adding file {_file} to be uploaded to remote context')
            else:
                logger.debug(f'file {_file} doesn\'t exist in the disk')

    if 'peas' in pea_args:
        uses_files = set()
        pymodules_files = set()

        for current_pea in pea_args['peas']:
            for _arg in ['uses', 'uses_before', 'uses_after']:
                _file_adder(_file=current_pea[_arg],
                            _file_list=uses_files)

            _file_adder(_file=current_pea['py_modules'],
                        _file_list=pymodules_files)

        if uses_files:
            for current_file in uses_files:
                with open(current_file) as f:
                    result = ruamel.yaml.round_trip_load(f)

                if 'metas' in result and 'py_modules' in result['metas']:
                    _file_adder(_file=result['metas']['py_modules'],
                                _file_list=pymodules_files)

        return uses_files, pymodules_files


class PodAPI:

    def __init__(self,
                 host: str,
                 port: int,
                 logger):
        self.logger = logger
        self.base_url = f'http://{host}:{port}/v1'
        self.alive_url = f'{self.base_url}/alive'
        self.upload_url = f'{self.base_url}/upload'
        self.pod_url = f'{self.base_url}/pod'
        self.log_url = f'{self.base_url}/log'
        try:
            import requests
        except (ImportError, ModuleNotFoundError):
            self.logger.critical('missing "requests" dependency, please do pip install "jina[http]"'
                                 'to enable remote Pod invocation')

    def is_alive(self):
        import requests
        try:
            r = requests.get(url=self.alive_url)
            if r.status_code == requests.codes.ok:
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False

    def upload(self, pea_args):
        try:
            import requests
            _uses_files, _pymodules_files = fetch_files_from_yaml(pea_args=pea_args,
                                                                  logger=self.logger)

            with ExitStack() as file_stack:
                files = []
                if _uses_files:
                    files.extend([('uses_files', file_stack.enter_context(open(fname, 'rb')))
                                  for fname in _uses_files])
                if _pymodules_files:
                    files.extend([('pymodules_files', file_stack.enter_context(open(fname, 'rb')))
                                  for fname in _pymodules_files])
                if files:
                    headers = {'content-type': 'multipart/form-data'}
                    r = requests.put(url=self.upload_url,
                                     files=files)
                    if r.status_code == requests.codes.ok:
                        self.logger.info(f'Got status {colored(r.json()["status"], "green")} from remote pod')

        except Exception as e:
            self.logger.error(f'got an error while uploading context files to remote pod {repr(e)}')

    def create(self, pea_args: Dict):
        import requests
        try:
            r = requests.put(url=self.pod_url,
                             json=pea_args)
            if r.status_code == requests.codes.ok:
                return r.json()['pod_id']
            return False
        except requests.exceptions.ConnectionError:
            return False

    def log(self, pod_id):
        # This will change with fluentd
        import requests
        try:
            r = requests.get(url=f'{self.log_url}/?pod_id={pod_id}',
                             stream=True)
            for log_line in r.iter_content():
                if log_line:
                    self.logger.info(f'🌏 {log_line}')

        except requests.exceptions.ConnectionError:
            return False

    def delete(self, pod_id):
        import requests
        try:
            r = requests.delete(url=f'{self.pod_url}/?pod_id={pod_id}')
            if r.status_code == requests.codes.ok:
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False


class RemoteMutablePod(BasePea):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API

    """
    def configure_pod_api(self):
        try:
            self.pod_host, self.pod_port = self.args['peas'][0].host, self.args['peas'][0].port_expose
            self.logger.info(f'got host {self.pod_host} and port {self.pod_port} for remote jinad pod')
        except (KeyError, AttributeError):
            self.logger.error('unable to fetch host & port of remote pod\'s REST interface')
            self.is_shutdown.set()

        self.pod_api = PodAPI(logger=self.logger,
                              host=self.pod_host,
                              port=self.pod_port)

    def loop_body(self):
        self.configure_pod_api()
        if self.pod_api.is_alive():
            self.logger.success('connected to the remote pod via jinad')

            pea_args = namespace_to_dict(self.args)
            self.pod_api.upload(pea_args=pea_args)
            self.pod_id = self.pod_api.create(pea_args=pea_args)
            if self.pod_id:
                self.logger.success(f'created remote pod with id {colored(self.pod_id, "cyan")}')
                self.set_ready()
                self.pod_api.log(pod_id=self.pod_id)
            else:
                self.logger.error('remote pod creation failed')
        else:
            self.logger.error('couldn\'t connect to the remote jinad')
            self.is_shutdown.set()

    def close(self):
        if self.pod_api.is_alive():
            status = self.pod_api.delete(pod_id=self.pod_id)
            if status:
                self.logger.success(f'successfully closed pod with id {colored(self.pod_id, "cyan")}')
            else:
                self.logger.error('remote pod close failed')
        else:
            self.logger.error('remote jinad pod is not active')
