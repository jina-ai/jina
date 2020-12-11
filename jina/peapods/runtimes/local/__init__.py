from jina import __ready_msg__, __stop_msg__
from jina.peapods.runtimes import RunTime
from jina.peapods import Pea

__all__ = ['LocalRunTime']


class LocalRunTime(RunTime):

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            with Pea(self.args) as pea:
                self.set_ready()
                self.logger.success(__ready_msg__)
                pea.run()
        finally:
            # if an exception occurs this unsets ready and shutting down
            self.unset_ready()
            self.logger.success(__stop_msg__)
            self.set_shutdown()
