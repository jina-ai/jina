import argparse

from .base import BaseRuntime
from ..zmq import Zmqlet, send_ctrl_message


class ZMQRuntime(BaseRuntime):

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr = Zmqlet.get_ctrl_address(self.args.host, self.args.port_ctrl, self.args.ctrl_with_ipc)[0]

    def cancel(self):
        send_ctrl_message(self.ctrl_addr, 'TERMINATE', timeout=self.args.timeout_ctrl)

    @property
    def status(self):
        return send_ctrl_message(self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl)

    @property
    def is_ready(self) -> bool:
        status = self.status
        return status and status.is_ready
