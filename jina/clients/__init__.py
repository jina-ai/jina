__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .python import PyClient, InputFnType
from .python.helper import callback_exec, pprint_routes
from ..helper import get_parsed_args
from ..parser import set_client_cli_parser


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
    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser())
    return PyClient(args)
