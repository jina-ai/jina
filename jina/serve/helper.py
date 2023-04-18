import functools
import inspect
import typing
from typing import Any, Dict, List, Optional, Tuple, Union

import grpc
#Test

from jina.helper import convert_tuple_to_list

if typing.TYPE_CHECKING:
    from prometheus_client.context_managers import Timer
    from prometheus_client import Summary

from contextlib import nullcontext


def _get_summary_time_context_or_null(
    summary_metric: Optional['Summary'],
) -> Union[nullcontext, 'Timer']:
    """
    helper function to either get a time context or a nullcontext if the summary metric is None
    :param summary_metric: An optional metric
    :return: either a Timer context or a nullcontext
    """
    return summary_metric.time() if summary_metric else nullcontext()


def wrap_func(cls, func_lst, wrapper, **kwargs):
    """Wrapping a class method only once, inherited but not overridden method will not be wrapped again

    :param cls: class
    :param func_lst: function list to wrap
    :param wrapper: the wrapper
    :param kwargs: extra wrapper kwargs
    """
    for f_name in func_lst:
        if hasattr(cls, f_name) and all(
            getattr(cls, f_name) != getattr(i, f_name, None) for i in cls.mro()[1:]
        ):
            setattr(cls, f_name, wrapper(getattr(cls, f_name), **kwargs))


def store_init_kwargs(
    func: typing.Callable, taboo: Optional[typing.Set] = None
) -> typing.Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML
    :param func: the function to decorate
    :param taboo: class taboo set of parameters
    :return: the wrapped function
    """
    taboo = taboo or {}

    @functools.wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError('this decorator should only be used on __init__ method')
        all_pars = inspect.signature(func).parameters
        tmp = {k: v.default for k, v in all_pars.items() if k not in taboo}
        tmp_list = [k for k in all_pars.keys() if k not in taboo]
        # set args by aligning tmp_list with arg values
        for k, v in zip(tmp_list, args):
            tmp[k] = v
        # set kwargs
        for k, v in kwargs.items():
            if k in tmp:
                tmp[k] = v
        if hasattr(self, '_init_kwargs_dict'):
            self._init_kwargs_dict.update(tmp)
        else:
            self._init_kwargs_dict = tmp
        convert_tuple_to_list(self._init_kwargs_dict)
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper


def extract_trailing_metadata(error: grpc.aio.AioRpcError) -> Optional[str]:
    '''Return formatted string of the trailing metadata if exists otherwise return None
    :param error: AioRpcError
    :return: string of Metadata or None
    '''
    if type(error) == grpc.aio.AioRpcError:
        trailing_metadata = error.trailing_metadata()
        if trailing_metadata and len(trailing_metadata):
            return f'trailing_metadata={trailing_metadata}'

    return None


def format_grpc_error(error: grpc.aio.AioRpcError) -> str:
    '''Adds grpc context trainling metadata if available
    :param error: AioRpcError
    :return: formatted error
    '''
    default_string = str(error)
    trailing_metadata = extract_trailing_metadata(error)
    if trailing_metadata:
        return f'{default_string}\n{trailing_metadata}'

    return default_string


def get_default_grpc_options() -> List[Tuple[str, Any]]:
    """
    Returns a list of default options used for creating grpc channels.
    Documentation is here https://github.com/grpc/grpc/blob/master/include/grpc/impl/codegen/grpc_types.h
    :returns: list of tuples defining grpc parameters
    """

    return [
        ('grpc.max_send_message_length', -1),
        ('grpc.max_receive_message_length', -1),
        # for the following see this blog post for the choice of default value https://cs.mcgill.ca/~mxia2/2019/02/23/Using-gRPC-in-Production/
        ('grpc.keepalive_time_ms', 9999),
        # send keepalive ping every 9 second, default is 2 hours.
        ('grpc.keepalive_timeout_ms', 4999),
        # keepalive ping time out after 4 seconds, default is 20 seconds
        ('grpc.keepalive_permit_without_calls', True),
        # allow keepalive pings when there's no gRPC calls
        ('grpc.http1.max_pings_without_data', 0),
        # allow unlimited amount of keepalive pings without data
        ('grpc.http1.min_time_between_pings_ms', 10000),
        # allow grpc pings from client every 9 seconds
        ('grpc.http1.min_ping_interval_without_data_ms', 5000),
        # allow grpc pings from client without data every 4 seconds
    ]


def get_server_side_grpc_options(
    additional_options: Optional[Union[list, Dict[str, Any]]] = None
) -> List[Tuple[str, Any]]:
    """transform dict of args into grpc option, will merge the args wit the default args
    :param additional_options: a dict of argument
    :return: grpc option i.e a list of tuple of key value
    """

    if additional_options:
        if type(additional_options) == list:
            grpc_options = get_default_grpc_options()
            grpc_options.extend(additional_options)
            return grpc_options
        elif type(additional_options) == dict:
            default_grpc_options = dict(get_default_grpc_options())
            merged_options = (
                {**default_grpc_options, **additional_options}
                if additional_options
                else default_grpc_options
            )  # merge new and default args
            return list(merged_options.items())

    return get_default_grpc_options()
