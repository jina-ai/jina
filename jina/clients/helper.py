__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from functools import wraps
from typing import Callable

from .. import Request
from ..enums import CallbackOnType
from ..excepts import BadClientCallback
from ..helper import colored
from ..importer import ImportExtensions
from ..proto import jina_pb2


def pprint_routes(resp: 'Request', stack_limit: int = 3):
    """Pretty print routes with :mod:`prettytable`, fallback to :func:`print`

    :param routes: list of :class:`jina_pb2.RouteProto` objects from Envelop
    :param status: the :class:`jina_pb2.StatusProto` object
    :param stack_limit: traceback limit
    :return:
    """
    from textwrap import fill

    routes = resp.routes

    header = [colored(v, attrs=['bold']) for v in ('Pod', 'Time', 'Exception')]

    # poorman solution
    table = []

    def add_row(x):
        for h, y in zip(header, x):
            table.append(f'{h}\n{y}\n{"-" * 10}')

    def visualize(x):
        print('\n'.join(x))

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

        add_row([f'{status_icon} {route.pod}',
                 f'{route.start_time.ToMilliseconds() - routes[0].start_time.ToMilliseconds()}ms',
                 fill(''.join(route.status.exception.stacks[-stack_limit:]), width=50,
                      break_long_words=False, replace_whitespace=False)])

    visualize(table)


def extract_field(resp, callback_on: 'CallbackOnType'):
    resp_body = getattr(resp, resp.WhichOneof('body'))

    if callback_on == CallbackOnType.BODY:
        return resp_body
    elif callback_on == CallbackOnType.DOCS:
        return resp_body.docs
    elif callback_on == CallbackOnType.GROUNDTRUTHS:
        return resp_body.groundtruths
    elif callback_on == CallbackOnType.REQUEST:
        return resp
    else:
        raise ValueError(f'callback_on={callback_on} is not supported, '
                         f'must be one of {list(CallbackOnType)}')


def safe_callback(func: Callable, continue_on_error: bool, logger) -> Callable:
    @wraps(func)
    def arg_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            err_msg = f'uncaught exception in callback {func.__name__}(): {repr(ex)}'
            if continue_on_error:
                logger.error(err_msg)
            else:
                raise BadClientCallback(err_msg) from ex

    return arg_wrapper


def callback_exec(response, on_done, on_error, on_always, continue_on_error, logger):
    if on_error and response.status.code >= jina_pb2.StatusProto.ERROR:
        safe_on_error = safe_callback(on_error, continue_on_error, logger)
        safe_on_error(response)
    elif on_done:
        safe_on_done = safe_callback(on_done, continue_on_error, logger)
        safe_on_done(response)
    if on_always:
        safe_on_always = safe_callback(on_always, continue_on_error, logger)
        safe_on_always(response)
