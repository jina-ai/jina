import argparse
import asyncio
from abc import ABC

from typing import Union

from ..zmq.base import ZMQRuntime


if False:
    import multiprocessing
    import threading


class AsyncZMQRuntime(ZMQRuntime):
    """
    Runtime procedure in the async manners.

    Base class of :class:`AsyncNewLoopRuntime`.
    """

    def __init__(
        self,
        args: 'argparse.Namespace',
        ctrl_addr: str,
        cancel_event: Union['multiprocessing.Event', 'threading.Event'],
        **kwargs
    ):
        super().__init__(args, ctrl_addr, **kwargs)
        self.is_cancel = cancel_event

    def run_forever(self):
        """Running method to block the main thread."""
        asyncio.run(self._loop_body())

    async def async_cancel(self):
        """An async method to cancel."""
        raise NotImplementedError

    async def async_run_forever(self):
        """The async method to run until it is stopped."""
        raise NotImplementedError

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        while True:
            if self.is_cancel.is_set():
                await self.async_cancel()
                return
            else:
                await asyncio.sleep(0.1)

    async def _loop_body(self):
        """Do NOT override this method when inheriting from :class:`GatewayPea`"""
        try:
            await asyncio.gather(self.async_run_forever(), self._wait_for_cancel())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')
        await self.async_cancel()


class AsyncNewLoopRuntime(AsyncZMQRuntime, ABC):
    """
    The runtime to start a new event loop.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.async_setup())

    def run_forever(self):
        """
        Running method to block the main thread.

        Run the event loop until a Future is done.
        """
        self._loop.run_until_complete(self._loop_body())

    def teardown(self):
        """Stop and close the event loop."""
        self._loop.stop()
        self._loop.close()
        super().teardown()

    async def async_setup(self):
        """The async method to setup."""
        pass
