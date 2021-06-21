import argparse
import os
from typing import Any, Tuple
import time
import multiprocessing
import threading

from .helper import _get_event, ConditionalEvent
from ... import __stop_msg__, __ready_msg__, __default_host__
from ...enums import PeaRoleType, RuntimeBackendType, SocketType, GatewayProtocolType
from ...excepts import RuntimeFailToStart, RuntimeTerminated
from ...helper import typename
from ...logging.logger import JinaLogger
from ..runtimes.jinad import JinadRuntime
from ..zmq import Zmqlet, send_ctrl_message

__all__ = ['BasePea']

if False:
    from ..runtimes.base import BaseRuntime


class BasePea:
    """
    :class:`BasePea` is a thread/process- container of :class:`BaseRuntime`. It leverages :class:`threading.Thread`
    or :class:`multiprocessing.Process` to manage the lifecycle of a :class:`BaseRuntime` object in a robust way.

    A :class:`BasePea` must be equipped with a proper :class:`Runtime` class to work.
    """

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__()  #: required here to call process/thread __init__
        self.worker = {
            RuntimeBackendType.THREAD: threading.Thread,
            RuntimeBackendType.PROCESS: multiprocessing.Process,
        }.get(getattr(args, 'runtime_backend', RuntimeBackendType.THREAD))(
            target=self.run
        )
        self.args = args
        self.daemon = args.daemon  #: required here to set process/thread daemon

        self.name = self.args.name or self.__class__.__name__
        self.is_ready = _get_event(self.worker)
        self.is_shutdown = _get_event(self.worker)
        self.ready_or_shutdown = ConditionalEvent(
            getattr(args, 'runtime_backend', RuntimeBackendType.THREAD),
            events_list=[self.is_ready, self.is_shutdown],
        )
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

        # arguments needed to create `runtime` and communicate with it in the `run` in the stack of the new process
        # or thread. Control address from Zmqlet has some randomness and therefore we need to make sure Pea knows
        # control address of runtime
        self.runtime_cls, self._is_remote_controlled = self._get_runtime_cls()

        # This logic must be improved specially when it comes to naming. It is about relative local/remote position
        # between the runtime and the `ZEDRuntime` it may control
        self._zed_runtime_ctrl_address = Zmqlet.get_ctrl_address(
            self.args.host, self.args.port_ctrl, self.args.ctrl_with_ipc
        )[0]
        self._local_runtime_ctrl_address = (
            Zmqlet.get_ctrl_address(None, None, True)[0]
            if self.runtime_cls == JinadRuntime
            else self._zed_runtime_ctrl_address
        )
        self._timeout_ctrl = self.args.timeout_ctrl

    def start(self):
        """Start the Pea.
        This method calls :meth:`start` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        .. #noqa: DAR201
        """
        self.worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def join(self, *args, **kwargs):
        """Joins the Pea.
        This method calls :meth:`join` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        :param args: extra positional arguments to pass to join
        :param kwargs: extra keyword arguments to pass to join
        """
        self.worker.join(*args, **kwargs)

    def terminate(self):
        """Terminate the Pea.
        This method calls :meth:`terminate` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        """
        if hasattr(self.worker, 'terminate'):
            self.worker.terminate()

    def _build_runtime(self):
        """
        Instantiates the runtime object

        :return: the runtime object
        """
        # This is due to the fact that JinadRuntime instantiates a Zmq server at local_ctrl_addr that will itself
        # send ctrl command
        # (TODO: Joan) Fix that in _wait_for_cancel from async runtime
        ctrl_addr = (
            self._local_runtime_ctrl_address
            if self.runtime_cls == JinadRuntime
            else self._zed_runtime_ctrl_address
        )
        return self.runtime_cls(self.args, ctrl_addr=ctrl_addr)

    def run(self):
        """Method representing the :class:`BaseRuntime` activity.

        This method overrides :meth:`run` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        .. note::
            :meth:`run` is running in subprocess/thread, the exception can not be propagated to the main process.
            Hence, please do not raise any exception here.
        """
        try:
            self._set_envs()
            runtime = self._build_runtime()
        except Exception as ex:
            self.logger.error(
                f'{ex!r} during {self.runtime_cls!r} initialization'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
        else:
            self.is_ready.set()
            try:
                runtime.run_forever()
            except RuntimeFailToStart as ex:
                self.logger.error(
                    f'{ex!r} during {self.runtime_cls.__init__!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )
            except RuntimeTerminated:
                self.logger.info(f'{runtime!r} is end')
            except KeyboardInterrupt:
                self.logger.info(f'{runtime!r} is interrupted by user')
            except (Exception, SystemError) as ex:
                self.logger.error(
                    f'{ex!r} during {runtime.run_forever!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

            try:
                runtime.teardown()
            except Exception as ex:
                self.logger.error(
                    f'{ex!r} during {runtime.teardown!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )
        finally:
            self.is_shutdown.set()
            self.is_ready.clear()
            self._unset_envs()

    def activate_runtime(self):
        """ Send activate control message. """
        if self._dealer:
            send_ctrl_message(
                self._zed_runtime_ctrl_address, 'ACTIVATE', timeout=self._timeout_ctrl
            )

    def _deactivate_runtime(self):
        """Send deactivate control message. """
        if self._dealer:
            send_ctrl_message(
                self._zed_runtime_ctrl_address, 'DEACTIVATE', timeout=self._timeout_ctrl
            )

    def _cancel_runtime(self):
        """Send terminate control message."""
        send_ctrl_message(
            self._local_runtime_ctrl_address, 'TERMINATE', timeout=self._timeout_ctrl
        )

    def wait_start_success(self):
        """Block until all peas starts successfully.

        If not success, it will raise an error hoping the outer function to catch it
        """
        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3
        if self.ready_or_shutdown.event.wait(_timeout):
            if self.is_shutdown.is_set():
                # return too early and the shutdown is set, means something fails!!
                if self.args.quiet_error:
                    self.logger.critical(
                        f'fail to start {self!r} because {self.runtime_cls!r} throws some exception, '
                        f'remove "--quiet-error" to see the exception stack in details'
                    )
                raise RuntimeFailToStart
            else:
                self.logger.success(__ready_msg__)
        else:
            _timeout = _timeout or -1
            self.logger.warning(
                f'{self.runtime_cls!r} timeout after waiting for {self.args.timeout_ready}ms, '
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
                self._deactivate_runtime()
                time.sleep(0.1)
                self._cancel_runtime()
                self.is_shutdown.wait()
            except Exception as ex:
                self.logger.error(
                    f'{ex!r} during {self._deactivate_runtime!r}'
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

    def _get_runtime_cls(self) -> Tuple[Any, bool]:
        is_remote_controlled = False
        if self.args.host != __default_host__:
            self.args.runtime_cls = 'JinadRuntime'
            is_remote_controlled = True
        if self.args.runtime_cls == 'ZEDRuntime' and self.args.uses.startswith(
            'docker://'
        ):
            self.args.runtime_cls = 'ContainerRuntime'
        if hasattr(self.args, 'protocol'):
            self.args.runtime_cls = {
                GatewayProtocolType.GRPC: 'GRPCRuntime',
                GatewayProtocolType.WEBSOCKET: 'WebSocketRuntime',
                GatewayProtocolType.HTTP: 'HTTPRuntime',
            }[self.args.protocol]
        from ..runtimes import get_runtime

        v = get_runtime(self.args.runtime_cls)
        return v, is_remote_controlled

    @property
    def role(self) -> 'PeaRoleType':
        """Get the role of this pea in a pod


        .. #noqa: DAR201"""
        return self.args.pea_role

    @property
    def _is_inner_pea(self) -> bool:
        """Determine whether this is a inner pea or a head/tail


        .. #noqa: DAR201"""
        return self.role is PeaRoleType.SINGLETON or self.role is PeaRoleType.PARALLEL
