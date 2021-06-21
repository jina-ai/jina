import argparse
from abc import ABC

from ..base import BaseRuntime
from ...zmq import send_ctrl_message


class ZMQRuntime(BaseRuntime, ABC):
    """Runtime procedure leveraging ZMQ."""

    def __init__(self, args: 'argparse.Namespace', ctrl_addr: str):
        super().__init__(args)
        self.ctrl_addr = ctrl_addr

    @property
    def status(self):
        """
        Send get status control message.

        :return: control message.
        """
        return send_ctrl_message(
            self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl
        )

    @property
    def is_ready(self) -> bool:
        """
        Check if status is ready.

        :return: True if status is ready else False.
        """
        status = self.status
        return status and status.is_ready
