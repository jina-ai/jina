import argparse
from typing import Union, Dict

from jina.peapods.peas import PeaRoleType
from jina.peapods.zmq import Zmqlet, send_ctrl_message
from jina.peapods.runtimes import BaseRuntime

__all__ = ['RemoteRuntime']


class RemoteRuntime(BaseRuntime):

    def __init__(self, args: Union['argparse.Namespace', Dict], kind: str):
        super().__init__(args)
        self.kind = kind
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
        elif isinstance(self.args, argparse.Namespace):
            self.daemon = self.args.daemon
            self.all_ctrl_addr.append(self.ctrl_addr)

    @property
    def is_idle(self) -> bool:
        raise NotImplementedError

    def _monitor_remote(self):
        raise NotImplementedError

    def run(self):
        """Start the container loop. Will spawn a docker container with a BasePea running inside.
         It will communicate with the container to see when it is ready to receive messages from the rest
         of the flow and stream the logs from the pea in the container"""
        try:
            self._monitor_remote()
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            self.logger.info(f'Ended monitoring remote')

    def send_terminate_signal(self) -> None:
        """Gracefully close this pea and release all resources """
        if self.is_ready_event.is_set() and self.all_ctrl_addr:
            for ctrl_addr in self.all_ctrl_addr:
                send_ctrl_message(address=ctrl_addr, cmd='TERMINATE',
                                  timeout=self.ctrl_timeout)

    def close(self) -> None:
        # Needed to override from Runtime because this forces shutdown event to end monitoring remote
        self.send_terminate_signal()
        self.unset_ready()
        self.is_shutdown.set()
        self.logger.close()
        if not self.daemon:
            self.join()
