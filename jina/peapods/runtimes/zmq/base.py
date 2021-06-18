import argparse
from abc import ABC

from ..base import BaseRuntime
from ...zmq import Zmqlet, send_ctrl_message


class ZMQRuntime(BaseRuntime, ABC):
    """Runtime procedure leveraging ZMQ."""

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr = Zmqlet.get_ctrl_address(
            self.args.host, self.args.port_ctrl, self.args.ctrl_with_ipc
        )[0]

    @staticmethod
    def cancel(ctrl_addr, timeout_ctrl):
        """Send terminate control message.
        :param ctrl_addr: The control address to send control message to
        :param timeout_ctrl: The timeout for the communication
        """
        # TODO (Joan): Should these control messages be translated in `JinadRuntime` by `api` calls?
        send_ctrl_message(ctrl_addr, 'TERMINATE', timeout=timeout_ctrl)

    @staticmethod
    def activate(ctrl_addr, timeout_ctrl):
        """Send activate control message.
        :param ctrl_addr: The control address to send control message to
        :param timeout_ctrl: The timeout for the communication
        """
        # TODO (Joan): Should these control messages be translated in `JinadRuntime` by `api` calls?
        send_ctrl_message(ctrl_addr, 'ACTIVATE', timeout=timeout_ctrl)

    @staticmethod
    def deactivate(ctrl_addr, timeout_ctrl):
        """Send deactivate control message.
        :param ctrl_addr: The control address to send control message to
        :param timeout_ctrl: The timeout for the communication
        """
        # TODO (Joan): Should these control messages be translated in `JinadRuntime` by `api` calls?
        send_ctrl_message(ctrl_addr, 'DEACTIVATE', timeout=timeout_ctrl)

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
