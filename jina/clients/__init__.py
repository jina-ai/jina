__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import time
import asyncio
from typing import Dict, Union, Callable

from ..logging import JinaLogger
from ..peapods.pea import BasePea
from ..peapods.zmq import CtrlZmqlet
from ..excepts import GRPCServerError
from ..proto.serializer import RequestProto
from .python.helper import callback_exec, pprint_routes

if False:
    import argparse
    from ..types.request import Request
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


def py_client_runtime(mode, input_fn, output_fn, **kwargs) -> None:
    """ This method allows callback execution of client process in main process

    PyClient writes the response from servicer in a PAIR-BIND socket.
    Main process reads from it using PAIR-CONNECT.

    """
    from zmq.error import Again
    from ..parser import set_client_cli_parser
    from ..helper import get_parsed_args
    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser(), 'Client')

    # setting this manually to avoid exposing on CLI
    args.runtime = 'process'

    with JinaLogger(context='PyClientRuntime') as logger:
        with CtrlZmqlet(args=args, logger=logger, is_bind=False, is_async=False, timeout=10) as zmqlet:
            with PyClientRuntime(args, mode=mode, input_fn=input_fn, output_fn=output_fn,
                                 address=zmqlet.address, **kwargs):
                # sleeping for a second to allow the process, event loop & the sockets to start in the client process
                time.sleep(1)
                while True:
                    try:
                        msg = zmqlet.sock.recv()
                        if msg == b'TERMINATE':
                            # ideal way of exit, but PyClient socket might have closed before we recv it here
                            logger.debug('received terminate message from the client response stream')
                            zmqlet.sock.send_string('')
                            break
                        on_error = kwargs['on_error'] if 'on_error' in kwargs else pprint_routes
                        on_always = kwargs['on_always'] if 'on_always' in kwargs else None
                        grpc_response = RequestProto.FromString(msg)

                        callback_exec(response=grpc_response, on_done=output_fn, on_error=on_error,
                                      on_always=on_always, continue_on_error=args.continue_on_error,
                                      logger=logger)
                        zmqlet.sock.send_string('')

                    except Again:
                        logger.debug('PyClient\'s BIND socket is not open yet. waiting for some time!')
                        time.sleep(0.5)
                        continue


class PyClientRuntime(BasePea):
    """ This class allows `PyClient` to run in a different process/thread"""

    def __init__(self,
                 args: Union['argparse.Namespace', Dict],
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
        from .python import PyClient
        PyClient.configure_event_loop()
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

    def close(self) -> None:
        self.is_shutdown.wait()
        if not self.daemon:
            self.logger.close()
            self.join()
