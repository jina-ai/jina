__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from argparse import Namespace
from typing import Dict, Union, Optional, Any

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
    APIClass = PeaAPI

    def __init__(self, args: Union['Namespace', Dict]):
        super().__init__(args)
        if isinstance(self.args, Namespace):
            self.ctrl_timeout = self.args.timeout_ctrl

    @cached_property
    def remote_id(self) -> str:
        return self.spawn_remote(host=self.args.host, port=self.args.port_expose)

    def spawn_remote(self, host: str, port: int, **kwargs) -> Optional[str]:
        self.api = self.APIClass(host=host, port=port, logger=self.logger, **kwargs)

        if self.api.is_alive:
            pea_args = namespace_to_dict(self.args)
            if self.api.upload(pea_args, **kwargs):
                return self.api.create(pea_args, **kwargs)

    def loop_body(self):
        if self.remote_id:
            self.logger.success(f'created remote {self.api.kind} with id {colored(self.remote_id, "cyan")}')
            self.set_ready()
            self.api.log(self.remote_id, self.is_shutdown)
        else:
            self.logger.error(f'fail to create {typename(self)} remotely')

    def send_terminate_signal(self) -> None:
        """Gracefully close this pea and release all resources """
        if self.is_ready_event.is_set() and hasattr(self, 'ctrl_addr'):
            send_ctrl_message(address=self.ctrl_addr, cmd='TERMINATE',
                              timeout=self.ctrl_timeout)

    def close(self) -> None:
        self.send_terminate_signal()
        self.is_shutdown.set()
        self.logger.close()
        if not self.daemon:
            self.join()


class RemotePod(RemotePea):
    """REST based pod to be used while invoking remote Pod
    """

    APIClass = PodAPI

    def __init__(self, args: Union['Namespace', Dict]):
        super().__init__(args)
        self.all_ctrl_addr = []
        if isinstance(self.args, Dict):
            first_pea_args = self.args['peas'][0]
            self.ctrl_timeout = first_pea_args.timeout_ctrl
            self.daemon = first_pea_args.daemon
            if first_pea_args.name:
                self.name = first_pea_args.name
            if first_pea_args.role == PeaRoleType.PARALLEL:
                self.name = f'{self.name}-{first_pea_args.pea_id}'
            for args in self.args['peas']:
                ctrl_addr, _ = Zmqlet.get_ctrl_address(args.host, args.port_ctrl, args.ctrl_with_ipc)
                self.all_ctrl_addr.append(ctrl_addr)

        if isinstance(self.args, Namespace):
            self.daemon = self.args.daemon
            self.all_ctrl_addr.append(self.ctrl_addr)

    def spawn_remote(self, host: str, port: int, pod_type: str = 'cli', **kwargs) -> Optional[str]:
        return super().spawn_remote(host=host, port=port, pod_type=pod_type)

    def send_terminate_signal(self) -> None:
        """Gracefully close this pea and release all resources """
        if self.is_ready_event.is_set() and self.all_ctrl_addr:
            for ctrl_addr in self.all_ctrl_addr:
                send_ctrl_message(address=ctrl_addr, cmd='TERMINATE',
                                  timeout=self.ctrl_timeout)


class RemoteMutablePod(RemotePod):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API
    """

    @cached_property
    def remote_id(self) -> str:
        return self.spawn_remote(host=self.args['peas'][0].host, port=self.args['peas'][0].port_expose)

    def spawn_remote(self, host: str, port: int, pod_type: str = 'flow', **kwargs) -> Optional[str]:
        return super().spawn_remote(host=host, port=port, pod_type=pod_type)
