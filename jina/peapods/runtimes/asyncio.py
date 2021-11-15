import argparse
import asyncio
import signal
import time
from abc import ABC, abstractmethod
from typing import Union, Optional, TYPE_CHECKING

from grpc import RpcError

from .base import BaseRuntime
from ... import __windows__
from ...importer import ImportExtensions

from ..networking import GrpcConnectionPool
from ...types.message.common import ControlMessage

if TYPE_CHECKING:
    import multiprocessing
    import threading


class AsyncNewLoopRuntime(BaseRuntime, ABC):
    """
    The async runtime to start a new event loop.
    """

    def __init__(
        self,
        args: 'argparse.Namespace',
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        super().__init__(args, **kwargs)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.is_cancel = cancel_event or asyncio.Event()

        if not __windows__:
            # TODO: windows event loops don't support signal handlers
            try:
                for signame in {'SIGINT', 'SIGTERM'}:
                    self._loop.add_signal_handler(
                        getattr(signal, signame),
                        lambda *args, **kwargs: self.is_cancel.set(),
                    )
            except (ValueError, RuntimeError) as exc:
                self.logger.warning(
                    f' The runtime {self.__class__.__name__} will not be able to handle termination signals. '
                    f' {repr(exc)}'
                )
        else:
            with ImportExtensions(
                required=True,
                logger=self.logger,
                help_text='''If you see a 'DLL load failed' error, please reinstall `pywin32`.
                If you're using conda, please use the command `conda install -c anaconda pywin32`''',
            ):
                import win32api

            win32api.SetConsoleCtrlHandler(
                lambda *args, **kwargs: self.is_cancel.set(), True
            )

        self._loop.run_until_complete(self.async_setup())

    def run_forever(self):
        """
        Running method to block the main thread.

        Run the event loop until a Future is done.
        """
        self._loop.run_until_complete(self._loop_body())

    def teardown(self):
        """Call async_teardown() and stop and close the event loop."""
        self._loop.run_until_complete(self.async_teardown())
        self._loop.stop()
        self._loop.close()
        super().teardown()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        # handle terminate signals
        while not self.is_cancel.is_set():
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def _loop_body(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        try:
            await asyncio.gather(self.async_run_forever(), self._wait_for_cancel())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')

    def _cancel(self):
        """
        Signal the runtime to terminate
        """
        self.is_cancel.set()

    async def async_setup(self):
        """The async method to setup."""
        pass

    async def async_teardown(self):
        """The async method to clean up resources during teardown. This method should free all resources allocated during async_setup"""
        pass

    @abstractmethod
    async def async_cancel(self):
        """An async method to cancel async_run_forever."""
        ...

    @abstractmethod
    async def async_run_forever(self):
        """The async method to run until it is stopped."""
        ...

    # Static methods used by the Pea to communicate with the `Runtime` in the separate process

    @staticmethod
    def activate(**kwargs):
        """
        Activate the runtime, does not apply to these runtimes

        :param kwargs: extra keyword arguments
        """
        # does not apply to this types of runtimes
        pass

    @staticmethod
    def is_ready(ctrl_address: str, **kwargs) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control message needs to be sent
        :param kwargs: extra keyword arguments

        :return: True if status is ready else False.
        """

        try:
            GrpcConnectionPool.send_message_sync(ControlMessage('STATUS'), ctrl_address)
        except RpcError:
            return False
        return True

    @staticmethod
    def wait_for_ready_or_shutdown(
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        ctrl_address: str,
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or is ready
        :param kwargs: extra keyword arguments
        :return: True if is ready or it needs to be shutdown
        """
        timeout_ns = 1000000000 * timeout if timeout else None
        now = time.time_ns()
        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            if ready_or_shutdown_event.is_set() or AsyncNewLoopRuntime.is_ready(
                ctrl_address
            ):
                return True
            time.sleep(0.1)
        return False

    def _log_info_msg(self, msg):
        info_msg = self._get_info_string(msg)
        self.logger.debug(info_msg)

    def _get_info_string(self, msg):
        info_msg = f'recv {msg.envelope.request_type} '
        req_type = msg.envelope.request_type
        if req_type == 'DataRequest':
            info_msg += (
                f'({msg.envelope.header.exec_endpoint}) - ({msg.envelope.request_id}) '
            )
        elif req_type == 'ControlRequest':
            info_msg += f'({msg.request.command}) '
        return info_msg

    def _log_info_messages(self, messages):
        # just use the first message for logging
        info_msg = self._get_info_string(messages[0])
        info_msg += f' with {len(messages)} message parts'
        self.logger.debug(info_msg)
