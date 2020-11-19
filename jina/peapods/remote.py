__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from argparse import Namespace
from typing import Dict, Union, Type, Optional, Any
from .zmq import Zmqlet, send_ctrl_message
from .jinad import PeaAPI, PodAPI
from .pea import BasePea
from ..helper import colored, cached_property, typename
from ..enums import PeaRoleType
from ..proto import jina_pb2


def namespace_to_dict(args: Union[Dict[str, 'Namespace'], 'Namespace']) -> Dict[str, Any]:
    """ helper function to convert argparse.Namespace to json to be uploaded via REST """
    if isinstance(args, Namespace):
        return vars(args)
    elif isinstance(args, dict):
        pea_args = {}
        for k, v in args.items():
            if isinstance(v, Namespace):
                pea_args[k] = vars(v)
            elif isinstance(v, list):
                pea_args[k] = [vars(_) for _ in v]
            else:
                pea_args[k] = v
        return pea_args


class RemotePea(BasePea):
    """REST based Pea for remote Pea management

    # TODO: This shouldn't inherit BasePea, Needs to change to a runtime
    """
    APIClass = PeaAPI  # type: Type['JinadAPI']

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)

    @cached_property
    def remote_id(self) -> str:
        return self.spawn_remote(host=self.args.host, port=self.args.port_expose)

    def spawn_remote(self, host: str, port: int, **kwargs) -> Optional[str]:
        self.api = self.APIClass(host, port, self.logger, **kwargs)

        if self.api.is_alive:
            pea_args = namespace_to_dict(self.args)
            if self.api.upload(pea_args, **kwargs):
                return self.api.create(pea_args, **kwargs)

    def loop_body(self):
        if self.remote_id:
            try:
                self.logger.success(f'created remote {self.api.kind} with id {colored(self.remote_id, "cyan")}')
                self.set_ready()
                self.api.log(self.remote_id)
            finally:
                self.is_shutdown.set()
        else:
            self.logger.error(f'fail to create {typename(self)} remotely')
            self.is_shutdown.set()

    def delete_remote(self):
        if hasattr(self, 'api') and self.api.is_alive and self.remote_id:
            self.api.delete(self.remote_id)

    def close(self) -> None:
        self.send_terminate_signal()
        # TODO: I would rather wait for loop_body to finish but it seems to go on forever


class RemotePod(RemotePea):
    """REST based pod to be used while invoking remote Pod
    """

    APIClass = PodAPI  # type: Type['JinadAPI']

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)

        if isinstance(self.args, Dict):
            first_pea_args = self.args['peas'][0]
            self.daemon = first_pea_args.daemon
            if first_pea_args.name:
                self.name = first_pea_args.name
            if first_pea_args.role == PeaRoleType.PARALLEL:
                self.name = f'{self.name}-{first_pea_args.pea_id}'
            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(first_pea_args.host, first_pea_args.port_ctrl,
                                                                         first_pea_args.ctrl_with_ipc)

    def spawn_remote(self, host: str, port: int, pod_type: str = 'cli', **kwargs) -> Optional[str]:
        return super().spawn_remote(host, port, pod_type=pod_type)

    def send_terminate_signal(self) -> None:
        """Gracefully close this pea and release all resources """
        if self.is_ready_event.is_set() and hasattr(self, 'ctrl_addr'):
            send_ctrl_message(self.ctrl_addr, jina_pb2.RequestProto.ControlRequestProto.TERMINATE,
                              timeout=self.args['peas'][0].timeout_ctrl)


class RemoteMutablePod(RemotePod):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API
    """

    @cached_property
    def remote_id(self) -> str:
        return self.spawn_remote(host=self.args['peas'][0].host, port=self.args['peas'][0].port_expose)

    def spawn_remote(self, host: str, port: int, pod_type: str = 'flow', **kwargs) -> Optional[str]:
        return super().spawn_remote(host, port, pod_type=pod_type)
