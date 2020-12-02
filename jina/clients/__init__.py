__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
from typing import Dict, Union, Callable

from ..proto import jina_pb2
from ..peapods.pea import BasePea
from ..peapods.zmq import AsyncCtrlZmqlet, send_message_async, recv_message_async, send_ctrl_message

if False:
    from .python import PyClient, InputFnType


def py_client(**kwargs) -> 'PyClient':
    """A simple Python client for connecting to the gateway.

    For acceptable ``kwargs``, please refer to :command:`jina client --help`

    Example, assuming a Flow is "standby" on 192.168.1.100, with port_expose at 55555.

    .. highlight:: python
    .. code-block:: python

        from jina.clients import py_client

        # to test connectivity
        await py_client(host='192.168.1.100', port_expose=55555).dry_run()

        # to search
        await py_client(host='192.168.1.100', port_expose=55555).search(input_fn, output_fn)

        # to index
        await py_client(host='192.168.1.100', port_expose=55555).index(input_fn, output_fn)

    .. note::
        to perform `index`, `search` or `train`, py_client needs to be awaited, as it is a coroutine

    """
    from ..parser import set_client_cli_parser
    from ..helper import get_parsed_args
    from .python import PyClient
    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser(), 'Client')
    return PyClient(args)


def py_client_runtime(mode, input_fn, output_fn, **kwargs) -> 'PyClientRuntime':
    from ..parser import set_client_cli_parser
    from ..helper import get_parsed_args
    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser(), 'Client')

    # setting these manually to avoid exposing these args on CLI
    args.runtime = 'process'
    args.port_ctrl = None
    args.ctrl_with_ipc = True
    return PyClientRuntime(args, mode, input_fn, output_fn, **kwargs)


class PyClientRuntime(BasePea):
    """ This class allows PyClient to run in a different process/thread"""

    def __init__(self,
                 args: Union['argparse.Namespace', Dict],
                 mode: str,
                 input_fn: 'InputFnType',
                 output_fn: Callable[['Request'], None],
                 **kwargs):
        super().__init__(args)
        self.mode = mode
        self.input_fn = input_fn
        self.output_fn = output_fn
        self._kwargs = kwargs

    async def _loop_body(self):
        """
        Unlike other peas (gateway, remote), PyClientRuntime shouldn't wait for flow closure
        This should await `index`, `search` or `train` & then close itself, rather than relying on terminate signal
        """
        self.primary_task = asyncio.get_running_loop().create_task(
            getattr(self.grpc_client, self.mode)(self.input_fn, self.output_fn, **self._kwargs)
        )
        try:
            await self.primary_task
        except asyncio.CancelledError:
            self.logger.warning('')

    def loop_body(self):
        from .python import PyClient
        self.grpc_client = PyClient(args=self.args)
        self.is_ready_event.set()
        asyncio.get_event_loop().run_until_complete(self._loop_body())

    async def _loop_teardown(self):
        await self.grpc_client.close()

    def loop_teardown(self):
        if hasattr(self, 'grpc_client'):
            self.primary_task.cancel()
            asyncio.get_event_loop().run_until_complete(self._loop_teardown())

    def close(self) -> None:
        self.is_shutdown.wait()
        if not self.daemon:
            self.logger.close()
            self.join()
