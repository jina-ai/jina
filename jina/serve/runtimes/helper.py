import copy
from typing import Any, Dict, List, Tuple

from jina.serve.networking.utils import get_default_grpc_options

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


def _get_grpc_server_options(option_from_args: Dict) -> List[Tuple[str, Any]]:
    """transform dict of args into grpc option, will merge the args wit the default args
    :param option_from_args: a dict of argument
    :return: grpc option i.e a list of tuple of key value
    """

    default_grpc_options = dict(get_default_grpc_options())

    option_from_args = (
        {**default_grpc_options, **option_from_args}
        if option_from_args
        else default_grpc_options
    )  # merge new and default args

    return list(option_from_args.items())
