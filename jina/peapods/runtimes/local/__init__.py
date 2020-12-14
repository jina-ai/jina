import os
from typing import Dict, Union

from jina import __ready_msg__, __stop_msg__
from jina.peapods.runtimes import RunTime
from jina.peapods import Pea

__all__ = ['LocalRunTime']


class LocalRunTime(RunTime):

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.pea = Pea(self.args)
        self._envs = {'JINA_POD_NAME': self.name}

        if 'env' in self.args and self.args.env:
            self._envs.update(self.args.env)

    def set_environment_vars(self):
        """Set environment variable to this pea

        .. note::
            Please note that env variables are process-specific. Subprocess inherits envs from
            the main process. But Subprocess's envs do NOT affect the main process. It does NOT
            mess up user local system envs.

        .. warning::
            If you are using ``thread`` as backend, envs setting will likely be overidden by others
        """
        if self._envs:
            if self.args.runtime == 'thread':
                self.logger.warning('environment variables should not be set when runtime="thread". '
                                    f'ignoring all environment variables: {self._envs}')
            else:
                for k, v in self._envs.items():
                    os.environ[k] = v

    def unset_environment_vars(self):
        if self._envs and self.args.runtime != 'thread':
            for k in self._envs.keys():
                os.unsetenv(k)

    @property
    def is_idle(self) -> bool:
        return self.pea.is_idle

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            self.set_environment_vars()
            with self.pea as pea:
                # TODO: set ready must be done by having a thread or corouting checking the status or passing multiprocessing event to the pea
                self.set_ready()
                self.logger.success(__ready_msg__)
                pea.run()
        except Exception as ex:
            self.logger.info(f'runtime run caught {repr(ex)}')
        finally:
            # if an exception occurs this unsets ready and shutting down
            self.unset_environment_vars()
            self.unset_ready()
            self.logger.success(__stop_msg__)
            self.set_shutdown()
