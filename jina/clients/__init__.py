__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import warnings

from zmq import Again

from .python.helper import callback_exec, pprint_routes
from .python.runtime import PyClientRuntime
from .. import Request
from ..helper import get_parsed_args
from ..logging import JinaLogger
from ..parser import set_client_cli_parser
from ..peapods.zmq import CtrlZmqlet

if False:
    from .python import PyClient, InputFnType


def py_client_old(**kwargs) -> 'PyClient':
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

    warnings.warn('this method is depreciated after 0.8.3, use "py_client" instead', DeprecationWarning)
    from ..parser import set_client_cli_parser
    from ..helper import get_parsed_args
    from .python import PyClient
    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser(), 'Client')
    return PyClient(args)


def py_client(mode, input_fn, output_fn, **kwargs) -> None:
    """ This method allows callback execution of client process in main process

    PyClient writes the response from servicer in a PAIR-BIND socket.
    Main process reads from it using PAIR-CONNECT.

    """

    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser(), 'Client')

    # setting this manually to avoid exposing on CLI
    args.runtime = 'process'
    on_error = kwargs['on_error'] if 'on_error' in kwargs else pprint_routes
    on_always = kwargs['on_always'] if 'on_always' in kwargs else None

    with JinaLogger(context='PyClientRuntime') as logger, \
            CtrlZmqlet(logger=logger, is_bind=False, is_async=False, timeout=10000) as zmqlet, \
            PyClientRuntime(args, mode=mode, input_fn=input_fn, output_fn=output_fn,
                            address=zmqlet.address, **kwargs):
        # note: we don't use async zmq context here on the main process
        while True:
            try:
                msg = zmqlet.sock.recv()
                if msg == b'TERMINATE':
                    # ideal way of exit, but PyClient socket might have closed before we recv it here
                    logger.debug('received terminate message from the client response stream')
                    zmqlet.sock.send_string('')
                    break
                else:
                    callback_exec(response=Request(msg), on_done=output_fn, on_error=on_error,
                                  on_always=on_always, continue_on_error=args.continue_on_error,
                                  logger=logger)
                    zmqlet.sock.send_string('')
            except Again:
                logger.warning(f'waited for 10 secs for PyClient to respond. breaking')
                break
