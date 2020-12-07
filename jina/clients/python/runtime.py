import asyncio
from argparse import Namespace
from typing import Union, Dict, Callable

from . import PyClient, InputFnType
from ...excepts import GRPCServerError
from ...helper import configure_event_loop
from ...peapods.pea import BasePea
from ...types.request import Request


class PyClientRuntime(BasePea):
    """ This class allows `PyClient` to run in a different process/thread"""

    def __init__(self,
                 args: Union['Namespace', Dict],
                 mode: str,
                 input_fn: 'InputFnType',
                 output_fn: Callable[['Request'], None],
                 address: str = None,
                 **kwargs):
        super().__init__(args)
        self.mode = mode
        self.input_fn = input_fn
        self.output_fn = output_fn
        self._address = address
        self._kwargs = kwargs

    async def _loop_body(self):
        """
        Unlike other peas (gateway, remote), PyClientRuntime shouldn't wait for flow closure
        This should await `index`, `search` or `train` & then close itself, rather than relying on terminate signal
        """
        try:
            await self.grpc_client.__aenter__()
        except GRPCServerError:
            self.logger.error('couldn\'t connect to PyClient. exiting')
            self.loop_teardown()
            return
        self.primary_task = asyncio.get_running_loop().create_task(
            getattr(self.grpc_client, self.mode)(self.input_fn, self.output_fn, **self._kwargs)
        )
        try:
            await self.primary_task
        except asyncio.CancelledError:
            self.logger.debug(f'{self.mode} operation got cancelled manually')

    def loop_body(self):
        configure_event_loop()
        self.grpc_client = PyClient(args=self.args, address=self._address)
        self.is_ready_event.set()
        asyncio.get_event_loop().run_until_complete(self._loop_body())

    async def _loop_teardown(self):
        if not self.grpc_client.is_closed:
            await self.grpc_client.close()

    def loop_teardown(self):
        if hasattr(self, 'grpc_client'):
            if hasattr(self, 'primary_task'):
                if not self.primary_task.done():
                    self.primary_task.cancel()
                asyncio.get_event_loop().run_until_complete(self._loop_teardown())
            self.is_shutdown.set()

    def send_terminate_signal(self) -> None:
        pass