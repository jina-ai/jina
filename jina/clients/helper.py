"""Helper functions for clients in Jina."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from functools import wraps
from typing import Callable

from .. import Response
from ..excepts import BadClientCallback
from ..helper import colored
from ..importer import ImportExtensions
from ..logging import JinaLogger
from ..proto import jina_pb2


def pprint_routes(resp: 'Response', stack_limit: int = 3):
    """Pretty print routes with :mod:`prettytable`, fallback to :func:`print`.

    :param resp: the :class:`Response` object
    :param stack_limit: traceback limit
    :return:
    """
    from textwrap import fill

    routes = resp.routes

    header = [colored(v, attrs=['bold']) for v in ('Pod', 'Time', 'Exception')]

    with ImportExtensions(required=False):
        from prettytable import PrettyTable, ALL

        table = PrettyTable(field_names=header, align='l', hrules=ALL)
        add_row = table.add_row
        visualize = print

    for route in routes:
        status_icon = '🟢'
        if route.status.code == jina_pb2.StatusProto.ERROR:
            status_icon = '🔴'
        elif route.status.code == jina_pb2.StatusProto.ERROR_CHAINED:
            status_icon = '⚪'

        add_row(
            [
                f'{status_icon} {route.pod}',
                f'{route.start_time.ToMilliseconds() - routes[0].start_time.ToMilliseconds()}ms',
                fill(
                    ''.join(route.status.exception.stacks[-stack_limit:]),
                    width=50,
                    break_long_words=False,
                    replace_whitespace=False,
                ),
            ]
        )

    visualize(table)


def _safe_callback(func: Callable, continue_on_error: bool, logger) -> Callable:
    @wraps(func)
    def _arg_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            err_msg = f'uncaught exception in callback {func.__name__}(): {ex!r}'
            if continue_on_error:
                logger.error(err_msg)
            else:
                raise BadClientCallback(err_msg) from ex

    return _arg_wrapper


def callback_exec(
    response,
    on_done: Callable,
    on_error: Callable,
    on_always: Callable,
    continue_on_error: bool,
    logger: JinaLogger,
) -> None:
    """Execute the callback with the response.

    :param response: the response
    :param on_done: the on_done callback
    :param on_error: the on_error callback
    :param on_always: the on_always callback
    :param continue_on_error: whether to continue on error
    :param logger: a logger instance
    """
    if on_error and response.status.code >= jina_pb2.StatusProto.ERROR:
        _safe_callback(on_error, continue_on_error, logger)(response)
    elif on_done:
        _safe_callback(on_done, continue_on_error, logger)(response)
    if on_always:
        _safe_callback(on_always, continue_on_error, logger)(response)
