import argparse
from typing import Union, Dict

from jina.peapods.runtimes import RunTime

__all__ = ['RemoteRunTime']


class RemoteRunTime(RunTime):

    def __init__(self, args: Union['argparse.Namespace', Dict], kind: str):
        super().__init__(args)
        self.kind = kind

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
            self.unset_ready()
            self.is_shutdown.set()
