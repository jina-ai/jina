import argparse
import asyncio
import signal
from abc import ABC, abstractmethod
from typing import Union, Optional, TYPE_CHECKING

from ..base import BaseRuntime
from .... import __windows__
from ....importer import ImportExtensions

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
    def cancel(
        cancel_event: Union['multiprocessing.Event', 'threading.Event'], **kwargs
    ):
        """
        Signal the runtime to terminate
        :param cancel_event: the cancel event to set
        :param kwargs: extra keyword arguments
        """
        cancel_event.set()

    @staticmethod
    def activate(**kwargs):
        """
        Activate the runtime, does not apply to these runtimes

        :param kwargs: extra keyword arguments
        """
        # does not apply to this types of runtimes
        pass

    @staticmethod
    def get_control_address(host: str, port: str, **kwargs):
        """
        Get the control address for a runtime with a given host and port

        :param host: the host where the runtime works
        :param port: the control port where the runtime listens
        :param kwargs: extra keyword arguments
        :return: The corresponding control address
        """
        from ...zmq import Zmqlet

        # TODO: I think the control address with ipc from Gateway is not used anymore
        return Zmqlet.get_ctrl_address(host, port, True)[0]

    @staticmethod
    def wait_for_ready_or_shutdown(
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or succeeded
        :param kwargs: extra keyword arguments

        :return: True if is ready or it needs to be shutdown
        """
        return ready_or_shutdown_event.wait(timeout)
