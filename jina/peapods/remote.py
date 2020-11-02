__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from pathlib import Path
from argparse import Namespace
from contextlib import ExitStack
from typing import Callable, Dict, List, Tuple, Union

import grpc
import ruamel.yaml

from .pea import BasePea
from .jinad import PeaAPI, PodAPI
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


# class RemotePod(RemotePea):
#     """A RemotePod that spawns a remote :class:`BasePod`
#     Useful in Jina CLI
#     """
#     remote_helper = PodSpawnHelper

#     def set_ready(self, resp):
#         _rep = getattr(resp, resp.WhichOneof('body'))
#         peas_args = mutable_pod_req2peas_args(_rep)
#         all_args = peas_args['peas'] + (
#             [peas_args['head']] if peas_args['head'] else []) + (
#                        [peas_args['tail']] if peas_args['tail'] else [])
#         for s in all_args:
#             s.host = self.args.host
#             self._remote.all_ctrl_addr.append(Zmqlet.get_ctrl_address(s)[0])
#         super().set_ready()


def namespace_to_dict(args: Union[Dict, Namespace]) -> Dict:
    """ helper function to convert argparse.Namespace to json to be uploaded via REST """
    if isinstance(args, Dict):
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

    if isinstance(args, Namespace):
        return vars(args)


class RemotePea(BasePea):
    """REST based Pea for remote Pea management """

    def is_alive(self):
        if not self.api.is_alive():
            self.logger.error('couldn\'t connect to the remote jinad')
            self.is_shutdown.set()
            return False
        else:
            self.logger.success('connected to the remote jinad')
            return True

    def configure_api(self, kind: str, host: str, port: int):
        self.logger.info(f'got host {host} and port {port} for remote jinad {kind}')
        self.api = PeaAPI(host, port, self.logger) if kind == 'pea' else PodAPI(host, port, self.logger)

    def loop_body(self):
        self.configure_api(kind='pea',
                           host=self.args.host,
                           port=self.args.port_expose)
        if self.is_alive():
            pea_args = namespace_to_dict(self.args)
            self.api.upload(pea_args=pea_args)
            self.pea_id = self.api.create(pea_args=pea_args)
            if not self.pea_id:
                self.logger.error('remote pea creation failed')
                self.is_shutdown.set()
                return
            self.logger.success(f'created remote pea with id {colored(self.pea_id, "cyan")}')
            self.set_ready()
            self.api.log(pea_id=self.pea_id)

    def loop_teardown(self):
        if self.is_alive():
            status = self.api.delete(pea_id=self.pea_id)
            if status:
                self.logger.success(f'successfully closed pea with id {colored(self.pea_id, "cyan")}')
            else:
                self.logger.error('remote pea close failed')


class RemoteMutablePod(RemotePea):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API

    """
    def loop_body(self):
        try:
            self.configure_api(kind='pod',
                               host=self.args['peas'][0].host,
                               port=self.args['peas'][0].port_expose)
        except (KeyError, AttributeError):
            self.logger.error('unable to fetch host & port of remote pod\'s REST interface')
            self.is_shutdown.set()

        if self.is_alive():
            pea_args = namespace_to_dict(self.args)
            self.api.upload(pea_args=pea_args)
            self.pod_id = self.api.create(pea_args=pea_args)
            if not self.pod_id:
                self.logger.error('remote pod creation failed')
                self.is_shutdown.set()
                return
            self.logger.success(f'created remote pod with id {colored(self.pod_id, "cyan")}')
            self.set_ready()
            self.api.log(pod_id=self.pod_id)

    def close(self):
        if self.is_alive():
            status = self.api.delete(pod_id=self.pod_id)
            if status:
                self.logger.success(f'successfully closed pod with id {colored(self.pod_id, "cyan")}')
            else:
                self.logger.error('remote pod close failed')
