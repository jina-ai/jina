import copy
from typing import Any, Dict, List, Tuple

_SPECIFIC_EXECUTOR_SEPARATOR = '__'


def _spit_key_and_executor_name(key_name: str) -> Tuple[str]:
    """Split a specific key into a key, name pair

    ex: 'key__my_executor' will be split into 'key', 'my_executor'

    :param key_name: key name of the param
    :return: return the split 'key', 'executor_name' for the key_name
    """
    key_split = key_name.split(_SPECIFIC_EXECUTOR_SEPARATOR)

    new_key_name = key_split.pop(-1)
    executor_name = ''.join(key_split)

    return new_key_name, executor_name


def _get_name_from_replicas_name(name: str) -> Tuple[str]:
    """return the original name without the replicas

    ex: 'exec1/rep-0' will be transform into 'exec1'

    :param name: name of the DataRequest
    :return: return the original name without the replicas
    """
    return name.split('/')[0]


def _is_param_for_specific_executor(key_name: str) -> bool:
    """Tell if a key is for a specific Executor

    ex: 'key' is for every Executor whereas 'my_executor__key' is only for 'my_executor'

    :param key_name: key name of the param
    :return: return True if key_name is for specific Executor, False otherwise
    """
    if _SPECIFIC_EXECUTOR_SEPARATOR in key_name:
        if key_name.startswith(_SPECIFIC_EXECUTOR_SEPARATOR) or key_name.endswith(
            _SPECIFIC_EXECUTOR_SEPARATOR
        ):
            return False
        return True
    else:
        return False


def _parse_specific_params(parameters: Dict, executor_name: str):
    """Parse the parameters dictionary to filter executor specific parameters

    :param parameters: dictionary container the parameters
    :param executor_name: name of the Executor
    :returns: the parsed parameters after applying filtering for the specific Executor
    """
    parsed_params = copy.deepcopy(parameters)

    for key in parameters:
        if _is_param_for_specific_executor(key):
            (
                key_name,
                key_executor_name,
            ) = _spit_key_and_executor_name(key)

            if key_executor_name == executor_name:
                parsed_params[key_name] = parameters[key]

            del parsed_params[key]

    specific_parameters = parameters.get(executor_name, None)
    if specific_parameters:
        parsed_params.update(**specific_parameters)

    return parsed_params


_DEFAULT_GRPC_OPTION = {
    'grpc.max_send_message_length': -1,
    'grpc.max_receive_message_length': -1,
    # for the following see this blog post for the choice of default value https://cs.mcgill.ca/~mxia3/2019/02/23/Using-gRPC-in-Production/
    'grpc.keepalive_time_ms': 10000,
    # send keepalive ping every 10 second, default is 2 hours.
    'grpc.keepalive_timeout_ms': 5000,
    # keepalive ping time out after 5 seconds, default is 20 seconds
    'grpc.keepalive_permit_without_calls': True,
    # allow keepalive pings when there's no gRPC calls
    'grpc.http2.max_pings_without_data': 0,
    # allow unlimited amount of keepalive pings without data
    'grpc.http2.min_time_between_pings_ms': 10000,
    # allow grpc pings from client every 10 seconds
    'grpc.http2.min_ping_interval_without_data_ms': 5000,
    # allow grpc pings from client without data every 5 seconds
    'grpc.so_reuseport': 1,
    # Multiple servers (processes or threads) can bind to the same port
}


def _get_grpc_server_options(option_from_args: Dict) -> List[Tuple[str, Any]]:
    """transform dict of args into grpc option, will merge the args wit the default args
    :param option_from_args: a dict of argument
    :return: grpc option i.e a list of tuple of key value
    """

    option_from_args = (
        {**_DEFAULT_GRPC_OPTION, **option_from_args}
        if option_from_args
        else _DEFAULT_GRPC_OPTION
    )  # merge new and default args

    return list(option_from_args.items())
