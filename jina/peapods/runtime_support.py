import argparse
from typing import Dict, Union

from .zmq import send_ctrl_message, Zmqlet
from ..enums import PeaRoleType
from ..excepts import PeaFailToStart

from ..helper import typename
from ..logging import JinaLogger
from . import Pea


class RunTimeSupport:
    def __init__(self, args: Union['argparse.Namespace', Dict]):
        self.args = args
        self.name = self.__class__.__name__

        if isinstance(self.args, argparse.Namespace):
            if self.args.name:
                self.name = f'support-{self.args.name}'
            elif self.args.role == PeaRoleType.PARALLEL:
                self.name = f'support-{self.name}-{self.args.pea_id}'

            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(self.args.host, self.args.port_ctrl,
                                                                         self.args.ctrl_with_ipc)
            self.logger = JinaLogger(self.name,
                                     log_id=self.args.log_id,
                                     log_config=self.args.log_config)
        else:
            self.logger = JinaLogger(self.name)

        self.pea = Pea(args, allow_remote=True)

    def send_terminate_signal(self) -> None:
        """Gracefully close this pea and release all resources """
        if self.pea.is_ready_event.is_set() and hasattr(self, 'ctrl_addr'):
            send_ctrl_message(self.ctrl_addr, 'TERMINATE',
                              timeout=self.args.timeout_ctrl)

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        if self.pea.is_ready_event.is_set() and getattr(self, 'ctrl_addr'):
            return send_ctrl_message(self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl)

    def start(self):
        self.pea.start()
        if isinstance(self.args, dict):
            _timeout = getattr(self.args['peas'][0], 'timeout_ready', -1)
        else:
            _timeout = getattr(self.args, 'timeout_ready', -1)

        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        if self.pea.ready_or_shutdown.wait(_timeout):
            if self.pea.is_shutdown.is_set():
                # return too early and the shutdown is set, means something fails!!
                self.logger.critical(f'fail to start {typename(self)} with name {self.name}, '
                                     f'this often means the executor used in the pod is not valid')
                raise PeaFailToStart
            return self
        else:
            raise TimeoutError(
                f'{typename(self)} with name {self.name} can not be initialized after {_timeout * 1e3}ms')

    def close(self) -> None:
        self.send_terminate_signal()
        self.pea.is_shutdown.wait()
        if not self.pea.daemon:
            self.logger.close()
            self.pea.join()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
