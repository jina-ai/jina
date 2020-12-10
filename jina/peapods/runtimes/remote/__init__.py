from argparse import Namespace
from typing import Union, Dict

from jina.peapods.runtimes import LocalRunTime


class RemoteRunTime(LocalRunTime):

    def __init__(self, args: Union['Namespace', Dict]):
        super().__init__(args)

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
            self._teardown()
            self.unset_ready()
            self.is_shutdown.set()
