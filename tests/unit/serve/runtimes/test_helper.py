from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import pytest

from jina.serve.helper import get_default_grpc_options
from jina.serve.runtimes.helper import (
    _get_name_from_replicas_name,
    _is_param_for_specific_executor,
    _parse_specific_params,
    _spit_key_and_executor_name,
)


@pytest.mark.parametrize(
    'key_name,is_specific',
    [
        ('key', False),
        ('key_1', False),
        ('executor__key', True),
        ('exec2__key_2', True),
        ('__results__', False),
        ('__banana__', False),
    ],
)
def test_is_specific_executor(key_name, is_specific):
    assert _is_param_for_specific_executor(key_name) == is_specific


@pytest.mark.parametrize(
    'full_key,key , executor',
    [
        ('executor__key', 'key', 'executor'),
        ('executor__key_1', 'key_1', 'executor'),
        ('executor_1__key', 'key', 'executor_1'),
    ],
)
def test_split_key_executor_name(full_key, key, executor):
    assert _spit_key_and_executor_name(full_key) == (key, executor)


@pytest.mark.parametrize(
    'param, parsed_param, executor_name',
    [
        (
            {'key': 1, 'executor__key': 2, 'wrong_executor__key': 3},
            {'key': 2},
            'executor',
        ),
        ({'executor__key': 2, 'wrong_executor__key': 3}, {'key': 2}, 'executor'),
        (
            {'a': 1, 'executor__key': 2, 'wrong_executor__key': 3},
            {'key': 2, 'a': 1},
            'executor',
        ),
        ({'key_1': 0, 'exec2__key_2': 1}, {'key_1': 0}, 'executor'),
    ],
)
def test_parse_specific_param(param, parsed_param, executor_name):
    assert _parse_specific_params(param, executor_name) == parsed_param


@pytest.mark.parametrize(
    'name_w_replicas,name', [('exec1/rep-0', 'exec1'), ('exec1', 'exec1')]
)
def test_get_name_from_replicas(name_w_replicas, name):
    assert _get_name_from_replicas_name(name_w_replicas) == name


def _custom_grpc_options(
    call_recording_mock: Mock,
    additional_options: Optional[Union[list, Dict[str, Any]]] = None,
) -> List[Tuple[str, Any]]:
    call_recording_mock()
    expected_grpc_option_keys = [
        'grpc.max_send_message_length',
        'grpc.keepalive_time_ms',
    ]

    if not additional_options:
        raise RuntimeError()
    if all([key not in additional_options.keys() for key in expected_grpc_option_keys]):
        raise RuntimeError()

    return get_default_grpc_options()
