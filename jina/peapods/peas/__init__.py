import argparse
import os
from typing import Type
import time

from .helper import _get_event, _make_or_event, PeaType
from ... import __stop_msg__, __ready_msg__, __default_host__
from ...enums import PeaRoleType, RuntimeBackendType, SocketType
from ...excepts import RuntimeFailToStart, RuntimeTerminated
from ...helper import typename
from ...logging.logger import JinaLogger

__all__ = ['BasePea']

if False:
    from ..runtimes.base import BaseRuntime


class BasePea(metaclass=PeaType):
    """
    :class:`BasePea` is a thread/process- container of :class:`BaseRuntime`. It leverages :class:`threading.Thread`
    or :class:`multiprocessing.Process` to manage the lifecycle of a :class:`BaseRuntime` object in a robust way.

    A :class:`BasePea` must be equipped with a proper :class:`Runtime` class to work.
    """

    runtime_cls = None  # type: Type['BaseRuntime']

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__()  #: required here to call process/thread __init__
        self.args = args
        self.daemon = args.daemon  #: required here to set process/thread daemon

        self.name = self.args.name or self.__class__.__name__
        self.is_ready = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready, self.is_shutdown)
        self.logger = JinaLogger(self.name, **vars(self.args))

        if self.args.runtime_backend == RuntimeBackendType.THREAD:
            self.logger.warning(
                f' Using Thread as runtime backend is not recommended for production purposes. It is '
                f'just supposed to be used for easier debugging. Besides the performance considerations, it is'
                f'specially dangerous to mix `Executors` running in different types of `RuntimeBackends`.'
            )

        self._envs = {'JINA_POD_NAME': self.name, 'JINA_LOG_ID': self.args.identity}
        if self.args.quiet:
            self._envs['JINA_LOG_CONFIG'] = 'QUIET'
        if self.args.env:
            self._envs.update(self.args.env)

        try:
            self.runtime = self._get_runtime_cls()(self.args)  # type: 'BaseRuntime'
        except Exception as ex:
            self.logger.error(
                f'{ex!r} during {self.runtime_cls.__init__!r}'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            raise RuntimeFailToStart from ex

    def run(self):
        """Method representing the :class:`BaseRuntime` activity.

        This method overrides :meth:`run` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        .. note::
            :meth:`run` is running in subprocess/thread, the exception can not be propagated to the main process.
            Hence, please do not raise any exception here.
        """
        self._set_envs()

        self.logger.info(f'starting {typename(self.runtime)}...')
        try:
            self.runtime.setup()
        except Exception as ex:
            self.logger.error(
                f'{ex!r} during {self.runtime.setup!r}'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
        else:
            self.is_ready.set()
            try:
                self.runtime.run_forever()
            except RuntimeTerminated:
                self.logger.info(f'{self.runtime!r} is end')
            except KeyboardInterrupt:
                self.logger.info(f'{self.runtime!r} is interrupted by user')
            except (Exception, SystemError) as ex:
                self.logger.error(
                    f'{ex!r} during {self.runtime.run_forever!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

            try:
                self.runtime.teardown()
            except Exception as ex:
                self.logger.error(
                    f'{ex!r} during {self.runtime.teardown!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )
        finally:
            self.is_shutdown.set()
            self.is_ready.clear()
            self._unset_envs()

    def start(self):
        """Start the Pea.

        This method overrides :meth:`start` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.


        .. #noqa: DAR201
        """

        super().start()  #: required here to call process/thread method
        if not self.args.noblock_on_start:
            self.wait_start_success()

        return self

    def wait_start_success(self):
        """Block until all peas starts successfully.

        If not success, it will raise an error hoping the outer function to catch it
        """
        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3
        if self.ready_or_shutdown.wait(_timeout):
            if self.is_shutdown.is_set():
                # return too early and the shutdown is set, means something fails!!
                if self.args.quiet_error:
                    self.logger.critical(
                        f'fail to start {self!r} because {self.runtime!r} throws some exception, '
                        f'remove "--quiet-error" to see the exception stack in details'
                    )
                raise RuntimeFailToStart
            else:
                self.logger.success(__ready_msg__)
        else:
            self.logger.warning(
                f'{self.runtime!r} timeout after waiting for {self.args.timeout_ready}ms, '
                f'if your executor takes time to load, you may increase --timeout-ready'
            )
            self.close()
            raise TimeoutError(
                f'{typename(self)}:{self.name} can not be initialized after {_timeout * 1e3}ms'
            )

    @property
    def _dealer(self):
        """Return true if this `Pea` must act as a Dealer responding to a Router
        .. # noqa: DAR201
        """
        return self.args.socket_in == SocketType.DEALER_CONNECT

    def close(self) -> None:
        """Close the Pea

        This method makes sure that the `Process/thread` is properly finished and its resources properly released
        """
        # wait 0.1s for the process/thread to end naturally, in this case no "cancel" is required this is required for
        # the is case where in subprocess, runtime.setup() fails and _finally() is not yet executed, BUT close() in the
        # main process is calling runtime.cancel(), which is completely unnecessary as runtime.run_forever() is not
        # started yet.
        self.join(0.1)

        # if that 1s is not enough, it means the process/thread is still in forever loop, cancel it
        if self.is_ready.is_set() and not self.is_shutdown.is_set():
            try:
                if self._dealer:
                    self.runtime.deactivate()
                    # this sleep is to make sure all the outgoing messages from the `router` reach the `pea` so that
                    # it does not block. Needs to be refactored
                    time.sleep(0.1)
                self.runtime.cancel()
                self.is_shutdown.wait()
            except Exception as ex:
                self.logger.error(
                    f'{ex!r} during {self.runtime.cancel!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

            # if it is not daemon, block until the process/thread finish work
            if not self.args.daemon:
                self.join()
        else:
            # if it fails to start, the process will hang at `join`
            if hasattr(self, 'terminate'):
                self.terminate()

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
                self.logger.warning(
                    'environment variables should not be set when runtime="thread".'
                )
            else:
                os.environ.update({k: str(v) for k, v in self._envs.items()})

    def _unset_envs(self):
        if self._envs and self.args.runtime_backend != RuntimeBackendType.THREAD:
            for k in self._envs.keys():
                os.unsetenv(k)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_runtime_cls(self) -> Type['BaseRuntime']:
        v = self.runtime_cls
        if not self.runtime_cls:
            if self.args.host != __default_host__:
                self.args.runtime_cls = 'JinadRuntime'
            if self.args.runtime_cls == 'ZEDRuntime' and self.args.uses.startswith(
                'docker://'
            ):
                self.args.runtime_cls = 'ContainerRuntime'

            from ..runtimes import get_runtime

            v = get_runtime(self.args.runtime_cls)
        return v

    @property
    def role(self) -> 'PeaRoleType':
        """Get the role of this pea in a pod


        .. #noqa: DAR201"""
        return self.args.pea_role

    @property
    def inner(self) -> bool:
        """Determine whether this is a inner pea or a head/tail


        .. #noqa: DAR201"""
        return self.role is PeaRoleType.SINGLETON or self.role is PeaRoleType.PARALLEL
