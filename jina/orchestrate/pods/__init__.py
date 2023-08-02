import argparse
import copy
import multiprocessing
import time
from abc import ABC, abstractmethod
from typing import Optional

from jina.constants import __ready_msg__, __stop_msg__, __windows__
from jina.enums import PodRoleType
from jina.excepts import RuntimeFailToStart, RuntimeRunForeverEarlyError
from jina.helper import typename
from jina.jaml import JAML
from jina.logging.logger import JinaLogger
from jina.orchestrate.pods.helper import ConditionalEvent, _get_event
from jina.parsers.helper import _update_gateway_args
from jina.serve.executors.run import run, run_raft
from jina.constants import RAFT_TO_EXECUTOR_PORT

__all__ = ['BasePod', 'Pod']


class BasePod(ABC):
    """
    :class:`BasePod` is an interface from which all the classes managing the lifetime of a Runtime inside a local process,
    container must inherit.

    It exposes the required APIs so that the `BasePod` can be handled by the `cli` api as a context manager or by a `Deployment`.

    What makes a BasePod a BasePod is that it manages the lifecycle of a Runtime (gateway or not gateway)
    """

    def __init__(self, args: 'argparse.Namespace'):
        self.args = args
        if self.args.pod_role == PodRoleType.GATEWAY:
            _update_gateway_args(self.args, gateway_load_balancer=getattr(self.args, 'gateway_load_balancer', False))
        self.args.parallel = getattr(self.args, 'shards', 1)
        self.name = self.args.name or self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(self.args))

        self._envs = {'JINA_DEPLOYMENT_NAME': self.name}
        if self.args.quiet:
            self._envs['JINA_LOG_CONFIG'] = 'QUIET'
        if self.args.env:
            self._envs.update(self.args.env)

        # arguments needed to create `runtime` and communicate with it in the `run` in the stack of the new process
        # or thread.f
        test_worker = multiprocessing.Process()
        self.is_ready = _get_event(test_worker)
        self.is_shutdown = _get_event(test_worker)
        self.cancel_event = _get_event(test_worker)
        self.is_started = _get_event(test_worker)
        self.is_signal_handlers_installed = _get_event(test_worker)
        self.ready_or_shutdown = ConditionalEvent(
            events_list=[self.is_ready, self.is_shutdown],
        )
        self.runtime_ctrl_address = self._get_control_address()
        self._timeout_ctrl = self.args.timeout_ctrl

    def _get_control_address(self):
        return f'{self.args.host}:{self.args.port[0]}'

    def close(self) -> None:
        """Close the Pod

        This method makes sure that the `Process` is properly finished and its resources properly released
        """
        self.logger.debug('waiting for ready or shutdown signal from runtime')
        if not self.is_shutdown.is_set() and self.is_started.is_set():
            try:
                self.logger.debug(f'terminate')
                self._terminate()
                if not self.is_shutdown.wait(
                        timeout=self._timeout_ctrl if not __windows__ else 1.0
                ):
                    if not __windows__:
                        raise Exception(
                            f'Shutdown signal was not received for {self._timeout_ctrl} seconds'
                        )
                    else:
                        self.logger.warning(
                            'Pod was forced to close after 1 second. Graceful closing is not available on Windows.'
                        )
            except Exception as ex:
                self.logger.error(
                    f'{ex!r} during {self.close!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )
        else:
            # here shutdown has been set already, therefore `run` will gracefully finish
            self.logger.debug(
                f'{"shutdown is already set" if self.is_shutdown.is_set() else "Runtime was never started"}. Runtime will end gracefully on its own'
            )
            if not self.is_shutdown.is_set():
                self.is_signal_handlers_installed.wait(timeout=self._timeout_ctrl if not __windows__ else 1.0) # waiting for is_signal_handlers_installed will make sure signal handlers are installed
            self._terminate()
        self.is_shutdown.set()
        self.logger.debug(__stop_msg__)
        self.logger.close()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _wait_for_ready_or_shutdown(self, timeout: Optional[float]):
        """
        Waits for the process to be ready or to know it has failed.

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        from jina.serve.runtimes.servers import BaseServer
        return BaseServer.wait_for_ready_or_shutdown(
            timeout=timeout,
            ready_or_shutdown_event=self.ready_or_shutdown.event,
            ctrl_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
            protocol=getattr(self.args, 'protocol', ["grpc"])[0],
            # for now protocol is not yet there part of Executor
        )

    def _fail_start_timeout(self, timeout):
        """
        Closes the Pod and raises a TimeoutError with the corresponding warning messages

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        _timeout = timeout or -1
        self.logger.warning(
            f'{self} timeout after waiting for {self.args.timeout_ready}ms, '
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
        """Block until all pods starts successfully.

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
        """
        Wait for the `Pod` to start successfully in a non-blocking manner
        """
        import asyncio
        from jina.serve.runtimes.servers import BaseServer

        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        timeout_ns = 1e9 * _timeout if _timeout else None
        now = time.time_ns()

        check_protocol = getattr(self.args, 'protocol', ["grpc"])[0]

        async def check_readiness_server():
            self.logger.debug(f'Checking readiness to {self.runtime_ctrl_address} with protocol {check_protocol}')
            ready = await BaseServer.async_is_ready(
                ctrl_address=self.runtime_ctrl_address,
                timeout=_timeout,
                protocol=check_protocol,
                logger=self.logger,
                # Executor does not have protocol yet
            )
            if ready:
                self.logger.debug(f'Server on {self.runtime_ctrl_address} with protocol {check_protocol} is ready')
            else:
                self.logger.debug(f'Server on {self.runtime_ctrl_address} with protocol {check_protocol} is not yet ready')
            return ready

        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            if (
                    self.ready_or_shutdown.event.is_set()
                    and (  # submit the health check to the pod, if it is
                    self.is_shutdown.is_set()  # a worker and not shutdown
                    or not self.args.pod_role == PodRoleType.WORKER
                    or (
                            await check_readiness_server()
                    )
            )
            ):
                self._check_failed_to_start()
                self.logger.debug(__ready_msg__)
                return
            else:
                await asyncio.sleep(0.1)

        self._fail_start_timeout(_timeout)

    @property
    def role(self) -> 'PodRoleType':
        """Get the role of this pod in a deployment
        .. #noqa: DAR201"""
        return self.args.pod_role

    @abstractmethod
    def start(self):
        """Start the BasePod.
        This method calls :meth:`start` in :class:`multiprocesssing.Process`.
        .. #noqa: DAR201
        """
        ...

    @abstractmethod
    def _terminate(self):
        ...

    @abstractmethod
    def join(self, *args, **kwargs):
        """Joins the BasePod. Wait for the BasePod to properly terminate

        :param args: extra positional arguments
        :param kwargs: extra keyword arguments
        """
        ...


class Pod(BasePod):
    """
    :class:`Pod` is a thread/process- container of :class:`BaseRuntime`. It leverages :class:`multiprocessing.Process` to manage the lifecycle of a :class:`BaseRuntime` object in a robust way.

    A :class:`Pod` must be equipped with a proper :class:`Runtime` class to work.
    """

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.runtime_cls = self._get_runtime_cls()
        cargs = None
        self.raft_worker = None
        if self.args.stateful and self.args.pod_role == PodRoleType.WORKER:
            cargs_stateful = copy.deepcopy(args)
            self.raft_worker = multiprocessing.Process(
                target=run_raft,
                kwargs={
                    'args': cargs_stateful,
                    'is_ready': self.is_ready,
                },
                name=self.name,
                daemon=True,
            )
            cargs = copy.deepcopy(cargs_stateful)

            if isinstance(cargs.port, int):
                cargs.port += RAFT_TO_EXECUTOR_PORT
            elif isinstance(cargs.port, list):
                cargs.port = [port + RAFT_TO_EXECUTOR_PORT for port in cargs.port]
        # if stateful, have a raft_worker
        self.worker = multiprocessing.Process(
            target=run,
            kwargs={
                'args': cargs or args,
                'name': self.name,
                'envs': self._envs,
                'is_started': self.is_started,
                'is_signal_handlers_installed': self.is_signal_handlers_installed,
                'is_shutdown': self.is_shutdown,
                'is_ready': self.is_ready,
                'runtime_cls': self.runtime_cls,
                'jaml_classes': JAML.registered_classes(),
            },
            name=self.name,
            daemon=False,
        )

    def start(self):
        """Start the Pod.
        This method calls :meth:`start` in :class:`multiprocesssing.Process`.
        .. #noqa: DAR201
        """
        self.worker.start()
        if self.raft_worker is not None:
            self.raft_worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def join(self, *args, **kwargs):
        """Joins the Pod.
        This method calls :meth:`join` in :class:`multiprocesssing.Process`.

        :param args: extra positional arguments to pass to join
        :param kwargs: extra keyword arguments to pass to join
        """
        self.logger.debug(f'joining the process')
        self.worker.join(*args, **kwargs)
        if self.raft_worker is not None:
            self.raft_worker.join(*args, **kwargs)
        self.logger.debug(f'successfully joined the process')

    def _terminate(self):
        """Terminate the Pod.
        This method calls :meth:`terminate` in :class:`multiprocesssing.Process`.
        """
        self.logger.debug(f'terminating the runtime process')
        self.worker.terminate()
        if self.raft_worker is not None:
            self.raft_worker.terminate()
        self.logger.debug(f'runtime process properly terminated')

    def _get_runtime_cls(self):
        from jina.orchestrate.pods.helper import update_runtime_cls

        update_runtime_cls(self.args)
        return self.args.runtime_cls
