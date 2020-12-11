import asyncio
from argparse import Namespace
from typing import Union, Dict, Callable

from . import PyClient, InputFnType
from ...excepts import GRPCServerError
from ...helper import configure_event_loop
from ...peapods.peas import BasePea
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
            self._teardown()
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

    def run(self):
        """Start the process to host the PyClient in a separate process"""
        try:
            # Every logger created in this process will be identified by the `Pod Id` and use the same name
            self.loop_body()
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            # this captures the general exception from the following places:
            # - self.zmqlet.recv_message
            # - self.zmqlet.send_message
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            # if an exception occurs this unsets ready and shutting down
            self._teardown()
            self.unset_ready()
            self.is_shutdown.set()

    async def _loop_teardown(self):
        if not self.grpc_client.is_closed:
            await self.grpc_client.close()

    def _teardown(self):
        if hasattr(self, 'grpc_client'):
            if hasattr(self, 'primary_task'):
                if not self.primary_task.done():
                    self.primary_task.cancel()
                asyncio.get_event_loop().run_until_complete(self._loop_teardown())
            self.is_shutdown.set()

    def close(self) -> None:
        self.is_shutdown.wait()
        if not self.daemon:
            self.logger.close()
            self.join()
