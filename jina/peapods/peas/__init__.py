import argparse
import multiprocessing
import os
import threading
import time
from typing import Any, Tuple, Union, Dict, Optional

from ...jaml import JAML
from .helper import _get_event, ConditionalEvent
from ... import __stop_msg__, __ready_msg__
from ...enums import PeaRoleType, RuntimeBackendType, SocketType
from ...excepts import RuntimeFailToStart, RuntimeRunForeverEarlyError
from ...helper import typename
from ...logging.logger import JinaLogger

__all__ = ['BasePea']


def run(
    args: 'argparse.Namespace',
    name: str,
    runtime_cls,
    envs: Dict[str, str],
    is_started: Union['multiprocessing.Event', 'threading.Event'],
    is_shutdown: Union['multiprocessing.Event', 'threading.Event'],
    is_ready: Union['multiprocessing.Event', 'threading.Event'],
    cancel_event: Union['multiprocessing.Event', 'threading.Event'],
    jaml_classes: Optional[Dict] = None,
):
    """Method representing the :class:`BaseRuntime` activity.

    This method is the target for the Pea's `thread` or `process`

    .. note::
        :meth:`run` is running in subprocess/thread, the exception can not be propagated to the main process.
        Hence, please do not raise any exception here.

    .. note::
        Please note that env variables are process-specific. Subprocess inherits envs from
        the main process. But Subprocess's envs do NOT affect the main process. It does NOT
        mess up user local system envs.

    .. warning::
        If you are using ``thread`` as backend, envs setting will likely be overidden by others

    .. note::
        `jaml_classes` contains all the :class:`JAMLCompatible` classes registered in the main process.
        When using `spawn` as the multiprocessing start method, passing this argument to `run` method re-imports
        & re-registers all `JAMLCompatible` classes.

    :param args: namespace args from the Pea
    :param name: name of the Pea to have proper logging
    :param runtime_cls: the runtime class to instantiate
    :param envs: a dictionary of environment variables to be set in the new Process
    :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
    :param is_shutdown: concurrency event to communicate runtime is terminated
    :param is_ready: concurrency event to communicate runtime is ready to receive messages
    :param cancel_event: concurrency event to receive cancelling signal from the Pea. Needed by some runtimes
    :param jaml_classes: all the `JAMLCompatible` classes imported in main process
    """
    logger = JinaLogger(name, **vars(args))

    def _unset_envs():
        if envs and args.runtime_backend != RuntimeBackendType.THREAD:
            for k in envs.keys():
                os.environ.pop(k, None)

    def _set_envs():
        if args.env:
            if args.runtime_backend == RuntimeBackendType.THREAD:
                logger.warning(
                    'environment variables should not be set when runtime="thread".'
                )
            else:
                os.environ.update({k: str(v) for k, v in envs.items()})

    try:
        _set_envs()
        runtime = runtime_cls(
            args=args,
            cancel_event=cancel_event,
        )
    except Exception as ex:
        logger.error(
            f'{ex!r} during {runtime_cls!r} initialization'
            + f'\n add "--quiet-error" to suppress the exception details'
            if not args.quiet_error
            else '',
            exc_info=not args.quiet_error,
        )
    else:
        is_started.set()
        with runtime:
            is_ready.set()
            runtime.run_forever()
    finally:
        _unset_envs()
        is_shutdown.set()
        logger.debug(f' Process terminated')


class BasePea:
    """
    :class:`BasePea` is a thread/process- container of :class:`BaseRuntime`. It leverages :class:`threading.Thread`
    or :class:`multiprocessing.Process` to manage the lifecycle of a :class:`BaseRuntime` object in a robust way.

    A :class:`BasePea` must be equipped with a proper :class:`Runtime` class to work.
    """

    def __init__(self, args: 'argparse.Namespace'):
        self.args = args
        # BACKWARDS COMPATIBILITY
        self.args.pea_id = self.args.shard_id
        self.args.parallel = self.args.shards
        self.name = self.args.name or self.__class__.__name__

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
        self.runtime_cls = self._get_runtime_cls()
        self._timeout_ctrl = self.args.timeout_ctrl
        self._set_ctrl_adrr()
        test_worker = {
            RuntimeBackendType.THREAD: threading.Thread,
            RuntimeBackendType.PROCESS: multiprocessing.Process,
        }.get(getattr(args, 'runtime_backend', RuntimeBackendType.THREAD))()
        self.is_ready = _get_event(test_worker)
        self.is_shutdown = _get_event(test_worker)
        self.cancel_event = _get_event(test_worker)
        self.is_started = _get_event(test_worker)
        self.ready_or_shutdown = ConditionalEvent(
            getattr(args, 'runtime_backend', RuntimeBackendType.THREAD),
            events_list=[self.is_ready, self.is_shutdown],
        )
        self.worker = {
            RuntimeBackendType.THREAD: threading.Thread,
            RuntimeBackendType.PROCESS: multiprocessing.Process,
        }.get(getattr(args, 'runtime_backend', RuntimeBackendType.THREAD))(
            target=run,
            kwargs={
                'args': args,
                'name': self.name,
                'envs': self._envs,
                'is_started': self.is_started,
                'is_shutdown': self.is_shutdown,
                'is_ready': self.is_ready,
                'cancel_event': self.cancel_event,
                'runtime_cls': self.runtime_cls,
                'jaml_classes': JAML.registered_classes(),
            },
        )
        self.daemon = self.args.daemon  #: required here to set process/thread daemon

    def _set_ctrl_adrr(self):
        """Sets control address for different runtimes"""
        self.runtime_ctrl_address = self.runtime_cls.get_control_address(
            host=self.args.host,
            port=self.args.port_ctrl,
            docker_kwargs=getattr(self.args, 'docker_kwargs', None),
        )

        if not self.runtime_ctrl_address:
            self.runtime_ctrl_address = f'{self.args.host}:{self.args.port_in}'

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
        self.logger.debug(f' Joining the process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f' Successfully joined the process')

    def terminate(self):
        """Terminate the Pea.
        This method calls :meth:`terminate` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        """
        if hasattr(self.worker, 'terminate'):
            self.logger.debug(f' terminating the runtime process')
            self.worker.terminate()
            self.logger.debug(f' runtime process properly terminated')

    def _retry_control_message(self, command: str, num_retry: int = 3):
        from ..zmq import send_ctrl_message

        for retry in range(1, num_retry + 1):
            self.logger.debug(f'Sending {command} command for the {retry}th time')
            try:
                send_ctrl_message(
                    self.runtime_ctrl_address,
                    command,
                    timeout=self._timeout_ctrl,
                    raise_exception=True,
                )
                break
            except Exception as ex:
                self.logger.warning(f'{ex!r}')
                if retry == num_retry:
                    raise ex

    def activate_runtime(self):
        """ Send activate control message. """
        self.runtime_cls.activate(
            logger=self.logger,
            socket_in_type=self.args.socket_in,
            control_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
        )

    def _cancel_runtime(self, skip_deactivate: bool = False):
        """
        Send terminate control message.

        :param skip_deactivate: Mark that the DEACTIVATE signal may be missed if set to True
        """
        self.runtime_cls.cancel(
            cancel_event=self.cancel_event,
            logger=self.logger,
            socket_in_type=self.args.socket_in,
            control_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
            skip_deactivate=skip_deactivate,
        )

    def _wait_for_ready_or_shutdown(self, timeout: Optional[float]):
        """
        Waits for the process to be ready or to know it has failed.

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        return self.runtime_cls.wait_for_ready_or_shutdown(
            timeout=timeout,
            ready_or_shutdown_event=self.ready_or_shutdown.event,
            ctrl_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
            shutdown_event=self.is_shutdown,
        )

    def _fail_start_timeout(self, timeout):
        """
        Closes the Pea and raises a TimeoutError with the corresponding warning messages

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        _timeout = timeout or -1
        self.logger.warning(
            f'{self.runtime_cls!r} timeout after waiting for {self.args.timeout_ready}ms, '
            f'if your executor takes time to load, you may increase --timeout-ready'
        )
        self.close()
        raise TimeoutError(
            f'{typename(self)}:{self.name} can not be initialized after {_timeout * 1e3}ms'
        )

    def _check_failed_to_start(self):
        """
        Raises a corresponding exception if failed to start
        """
        if self.is_shutdown.is_set():
            # return too early and the shutdown is set, means something fails!!
            if not self.is_started.is_set():
                raise RuntimeFailToStart
            else:
                raise RuntimeRunForeverEarlyError

    def wait_start_success(self):
        """Block until all peas starts successfully.

        If not success, it will raise an error hoping the outer function to catch it
        """
        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        if self._wait_for_ready_or_shutdown(_timeout):
            self._check_failed_to_start()
            self.logger.debug(__ready_msg__)
        else:
            self._fail_start_timeout(_timeout)

    async def async_wait_start_success(self):
        """Block until all peas starts successfully.

        If not success, it will raise an error hoping the outer function to catch it
        """
        import asyncio

        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        timeout_ns = 1e9 * _timeout if _timeout else None
        now = time.time_ns()
        while timeout_ns is None or time.time_ns() - now < timeout_ns:

            if self.ready_or_shutdown.event.is_set():
                self._check_failed_to_start()
                self.logger.debug(__ready_msg__)
                return
            else:
                await asyncio.sleep(0.1)

        self._fail_start_timeout(_timeout)

    @property
    def _is_dealer(self):
        """Return true if this `Pea` must act as a Dealer responding to a Router
        .. # noqa: DAR201
        """
        return self.args.socket_in == SocketType.DEALER_CONNECT

    def close(self) -> None:
        """Close the Pea

        This method makes sure that the `Process/thread` is properly finished and its resources properly released
        """
        # if that 1s is not enough, it means the process/thread is still in forever loop, cancel it
        self.logger.debug('waiting for ready or shutdown signal from runtime')
        terminated = False
        if self.is_ready.is_set() and not self.is_shutdown.is_set():
            try:
                self.logger.debug(f' Cancel runtime')
                self._cancel_runtime()
                self.logger.debug(f' Wait to shutdown')
                if not self.is_shutdown.wait(timeout=self._timeout_ctrl):
                    self.terminate()
                    terminated = True
                    time.sleep(0.1)
                    raise Exception(
                        f'Shutdown signal was not received for {self._timeout_ctrl}'
                    )
            except Exception as ex:
                self.logger.error(
                    f'{ex!r} during {self.close!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )
                if not terminated:
                    self.terminate()

            # if it is not daemon, block until the process/thread finish work
            if not self.args.daemon:
                self.join()
        elif self.is_shutdown.is_set():
            # here shutdown has been set already, therefore `run` will gracefully finish
            self.logger.debug(
                'shutdown is already set. Runtime will end gracefully on its own'
            )
            pass
        else:
            # sometimes, we arrive to the close logic before the `is_ready` is even set.
            # Observed with `gateway` when Pods fail to start
            self.logger.warning(
                'Pea is being closed before being ready. Most likely some other Pea in the Flow or Pod '
                'failed to start'
            )
            _timeout = self.args.timeout_ready
            if _timeout <= 0:
                _timeout = None
            else:
                _timeout /= 1e3
            self.logger.debug('waiting for ready or shutdown signal from runtime')
            if self._wait_for_ready_or_shutdown(_timeout):
                if not self.is_shutdown.is_set():
                    self._cancel_runtime(skip_deactivate=True)
                    if not self.is_shutdown.wait(timeout=self._timeout_ctrl):
                        self.terminate()
                        time.sleep(0.1)
                        raise Exception(
                            f'Shutdown signal was not received for {self._timeout_ctrl}'
                        )
            else:
                self.logger.warning(
                    'Terminating process after waiting for readiness signal for graceful shutdown'
                )
                # Just last resource, terminate it
                self.terminate()
                time.sleep(0.1)
        self.logger.debug(__stop_msg__)
        self.logger.close()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_runtime_cls(self) -> Tuple[Any, bool]:
        from .helper import update_runtime_cls
        from ..runtimes import get_runtime

        update_runtime_cls(self.args)
        return get_runtime(self.args.runtime_cls)

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
