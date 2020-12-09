from argparse import Namespace
from typing import Union, Dict, Optional

from .jinad import PeaAPI
from .. import BasePea
from ...zmq import send_ctrl_message
from ....helper import cached_property, namespace_to_dict, colored, typename


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

    def run(self):
        """Start the container loop. Will spawn a docker container with a BasePea running inside.
         It will communicate with the container to see when it is ready to receive messages from the rest
         of the flow and stream the logs from the pea in the container"""
        try:
            self.loop_body()
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            self._teardown()
            self.unset_ready()
            self.is_shutdown.set()

    def close(self) -> None:
        self.send_terminate_signal()
        self.is_shutdown.set()
        self.logger.close()
        if not self.daemon:
            self.join()
