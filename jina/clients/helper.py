"""Helper functions for clients in Jina."""

from functools import wraps
from typing import Callable

from jina.excepts import BadClientCallback, BadServer
from jina.helper import get_rich_console
from jina.logging.logger import JinaLogger
from jina.types.request.data import Response


def pprint_routes(resp: 'Response', stack_limit: int = 3):
    """Pretty print routes with :mod:`prettytable`, fallback to :func:`print`.

    :param resp: the :class:`Response` object
    :param stack_limit: traceback limit
    """
    routes = resp.routes

    from rich import box
    from rich.table import Table

    table = Table(box=box.SIMPLE)
    for v in ('Executor', 'Time', 'Exception'):
        table.add_column(v)
    from jina.proto import jina_pb2

    for route in routes:
        status_icon = '🟢'
        if route.status.code == jina_pb2.StatusProto.ERROR:
            status_icon = '🔴'

        table.add_row(
            f'{status_icon} {route.executor}',
            f'{route.start_time.ToMilliseconds() - routes[0].start_time.ToMilliseconds()}ms',
            ''.join(route.status.exception.stacks[-stack_limit:]),
        )

    console = get_rich_console()
    console.print(table)


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
    from jina.proto import jina_pb2

    if response.header.status.code >= jina_pb2.StatusProto.ERROR:
        if on_error:
            _safe_callback(on_error, continue_on_error, logger)(response)
        elif continue_on_error:
            logger.error(f'Server error: {response.header}')
        else:
            raise BadServer(response.header)
    elif on_done and response.header.status.code == jina_pb2.StatusProto.SUCCESS:
        _safe_callback(on_done, continue_on_error, logger)(response)
    if on_always:
        _safe_callback(on_always, continue_on_error, logger)(response)
