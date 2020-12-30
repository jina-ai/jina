import argparse
import os
from typing import Type

from .helper import _get_event, _make_or_event, PeaType
from ... import __stop_msg__, __ready_msg__
from ...enums import PeaRoleType, RuntimeBackendType
from ...excepts import RuntimeFailToStart, RuntimeTerminated
from ...helper import typename
from ...logging.logger import JinaLogger

__all__ = ['BasePea']

if False:
    from ..runtimes.base import BaseRuntime


class BasePea(metaclass=PeaType):
    runtime_cls = None  # type: Type['BaseRuntime']

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__()  #: required here to call process/thread __init__
        self.args = args
        self.daemon = args.daemon  #: required here to set process/thread daemon

        # set name
        self.name = self.args.name or self.__class__.__name__
        if args.pea_role == PeaRoleType.PARALLEL:
            self.name = f'{self.name}-{args.pea_id}'
        elif args.pea_role == PeaRoleType.SINGLETON:
            pass
        else:
            self.name = f'{self.name}-{str(args.pea_role).lower()}'

        self.is_ready = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready, self.is_shutdown)
        self.logger = JinaLogger(self.name,
                                 log_id=self.args.log_id,
                                 log_config=self.args.log_config)
        try:
            args.name = f'{self.name}-R'
            self.runtime = self._get_runtime_cls()(args)  # type: 'BaseRuntime'
        except Exception as ex:
            self.logger.error(f'{ex!r} during {self.runtime_cls.__init__!r}')
            raise RuntimeFailToStart from ex

    def run(self):
        """ Method representing the :class:`BaseRuntime` activity.
        """

        def _finally():
            self.is_shutdown.set()
            self.is_ready.clear()
            self._unset_envs()

        self._set_envs()

        try:
            self.runtime.setup()
        except Exception as ex:
            self.logger.error(f'{ex!r} during {self.runtime.setup!r}')
        else:
            self.is_ready.set()
            try:
                self.runtime.run_forever()
            except RuntimeTerminated:
                self.logger.info(f'{self.runtime!r} is end')
            except KeyboardInterrupt:
                self.logger.info(f'{self.runtime!r} is interrupted by user')
            except (Exception, SystemError) as ex:
                self.logger.error(f'{ex!r} during {self.runtime.run_forever!r}', exc_info=True)

            try:
                self.runtime.teardown()
            except Exception as ex:
                self.logger.error(f'{ex!r} during {self.runtime.teardown!r}')
        finally:
            _finally()

    def start(self):
        super().start()  #: required here to call process/thread method
        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        if self.ready_or_shutdown.wait(_timeout):
            if self.is_shutdown.is_set():
                # return too early and the shutdown is set, means something fails!!
                self.logger.critical(f'fail to start {self!r}, '
                                     f'this often means the runtime {self.runtime!r} throws some exception')
                raise RuntimeFailToStart
            else:
                self.logger.success(__ready_msg__)
        else:
            self.close()
            raise TimeoutError(
                f'{typename(self)}:{self.name} can not be initialized after {_timeout * 1e3}ms')

    def close(self) -> None:
        # wait 1s for the process/thread to end naturally, in this case no "cancel" is required this is required for
        # the is case where in subprocess, runtime.setup() fails and _finally() is not yet executed, BUT close() in the
        # main process is calling runtime.cancel(), which is completely unnecessary as runtime.run_forever() is not
        # started yet.
        self.join(1)

        # if that 1s is not enough, it means the process/thread is still in forever loop, cancel it
        if self.is_ready.is_set() and not self.is_shutdown.is_set():
            try:
                self.runtime.cancel()
                self.is_shutdown.wait()
            except Exception as ex:
                self.logger.error(f'{ex!r} during {self.runtime.cancel!r}')

            # if it is not daemon, block until the process/thread finish work
            if not self.args.daemon:
                self.join()

        self.logger.success(__stop_msg__)
        self.logger.close()

    def _set_envs(self):
        """Set environment variable to this pea

        .. note::
            Please note that env variables are process-specific. Subprocess inherits envs from
            the main process. But Subprocess's envs do NOT affect the main process. It does NOT
            mess up user local system envs.

        .. warning::
            If you are using ``thread`` as backend, envs setting will likely be overidden by others
        """
        if self.args.env:
            if self.args.runtime_backend == RuntimeBackendType.THREAD:
                self.logger.warning('environment variables should not be set when runtime="thread".')
            else:
                for k, v in self.args.env.items():
                    os.environ[k] = v

    def _unset_envs(self):
        if self.args.env and self.args.runtime_backend != RuntimeBackendType.THREAD:
            for k in self.args.env.keys():
                os.unsetenv(k)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_runtime_cls(self):
        v = self.runtime_cls
        if not v:
            from ..runtimes import get_runtime
            v = get_runtime(self.args.runtime_cls)
        return v

    @property
    def role(self) -> 'PeaRoleType':
        return self.args.pea_role
