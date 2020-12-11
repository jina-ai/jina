__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from argparse import Namespace
from typing import Dict, Union, Optional

from ..peas.remote import RemotePea
from ..peas.remote.jinad import PodAPI
from ..zmq import Zmqlet, send_ctrl_message
from ...enums import PeaRoleType
from ...helper import cached_property


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
