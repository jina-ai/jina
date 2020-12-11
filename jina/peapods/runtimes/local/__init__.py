from typing import Dict, Union

from jina import __ready_msg__, __stop_msg__
from jina.peapods.runtimes import RunTime
from jina.peapods import Pea

__all__ = ['LocalRunTime']


class LocalRunTime(RunTime):

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.pea = Pea(self.args)

    @property
    def is_idle(self) -> bool:
        return self.pea.is_idle

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            with self.pea as pea:
                # TODO: set ready must be done by having a thread or corouting checking the status or passing multiprocessing event to the pea
                self.set_ready()
                self.logger.success(__ready_msg__)
                pea.run()
        except Exception as ex:
            self.logger.info(f'runtime run caught {repr(ex)}')
        finally:
            # if an exception occurs this unsets ready and shutting down
            self.unset_ready()
            self.logger.success(__stop_msg__)
            self.set_shutdown()
