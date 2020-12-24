import argparse

from .base import BasePea
from ..zmq import send_ctrl_message, Zmqlet


class ZMQControlPea(BasePea):
    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(self.args.host,
                                                                     self.args.port_ctrl,
                                                                     self.args.ctrl_with_ipc)

    def serve_forever(self):
        pass

    def setup(self):
        pass

    def teardown(self):
        pass

    def cancel(self):
        return send_ctrl_message(self.ctrl_addr, 'TERMINATE', timeout=self.args.timeout_ctrl)
