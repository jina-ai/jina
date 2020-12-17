import argparse
import os
from typing import Dict, Union

from jina import __stop_msg__
from jina.peapods.runtimes import BaseRuntime
from jina.peapods.peas import BasePea

__all__ = ['LocalRuntime']


class LocalRuntime(BaseRuntime):

    """LocalRuntime is a process or thread providing the support to run different :class:`BasePea` locally.

        Inside the run method, the :class:`BasePea` is context managed to guarantee a robust closing of the Pea context
    """
    def __init__(self,
                 args: Union['argparse.Namespace', Dict],
                 pea_cls: 'BasePea' = BasePea):
        super().__init__(args)
        self._envs = {'JINA_POD_NAME': self.name,
                      'JINA_LOG_ID': self.args.log_id}

        if 'env' in self.args and self.args.env:
            self._envs.update(self.args.env)
        self.pea = pea_cls(self.args, ctrl_addr=self.ctrl_addr, ctrl_with_ipc=self.ctrl_with_ipc)

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
        """Start the request loop of this Runtime. It will start a BasePea as a context manager and call its
        main run entrypoint """
        try:
            self.set_environment_vars()
            with self.pea as pea:
                pea.run(self.is_ready_event)
        except Exception as ex:
            self.logger.info(f'runtime run caught {repr(ex)}')
        finally:
            # if an exception occurs this unsets ready and shutting down
            self.unset_environment_vars()
            self.unset_ready()
            self.logger.success(__stop_msg__)
            self.set_shutdown()
