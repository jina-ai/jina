import asyncio
import base64
import functools
import inspect
import json
import math
import os
import random
import re
import sys
import threading
import time
import urllib
import uuid
import warnings
from argparse import ArgumentParser, Namespace
from collections.abc import MutableMapping
from datetime import datetime
from itertools import islice
from socket import AF_INET, SOCK_STREAM, socket
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from rich.console import Console

from jina import __windows__

__all__ = [
    'batch_iterator',
    'parse_arg',
    'random_port',
    'random_identity',
    'random_uuid',
    'expand_env_var',
    'colored',
    'ArgNamespace',
    'is_valid_local_config_source',
    'cached_property',
    'typename',
    'get_public_ip',
    'get_internal_ip',
    'convert_tuple_to_list',
    'run_async',
    'deprecated_alias',
    'retry',
    'countdown',
    'CatchAllCleanupContextManager',
    'download_mermaid_url',
    'get_readable_size',
    'get_or_reuse_loop',
    'T',
    'get_rich_console',
]

T = TypeVar('T')
GATEWAY_NAME = 'gateway'


def deprecated_alias(**aliases):
    """
    Usage, kwargs with key as the deprecated arg name and value be a tuple, (new_name, deprecate_level).

    With level 0 means warning, level 1 means exception.

    For example:
        .. highlight:: python
        .. code-block:: python

            @deprecated_alias(
                input_fn=('inputs', 0),
                buffer=('input_fn', 0),
                callback=('on_done', 1),
                output_fn=('on_done', 1),
            )
            def some_function(inputs, input_fn, on_done):
                pass

    :param aliases: maps aliases to new arguments
    :return: wrapper
    """
    from jina.excepts import NotSupportedError

    def _rename_kwargs(func_name: str, kwargs, aliases):
        """
        Raise warnings or exceptions for deprecated arguments.

        :param func_name: Name of the function.
        :param kwargs: key word arguments from the function which is decorated.
        :param aliases: kwargs with key as the deprecated arg name and value be a tuple, (new_name, deprecate_level).
        """
        for alias, new_arg in aliases.items():
            if not isinstance(new_arg, tuple):
                raise ValueError(
                    f'{new_arg} must be a tuple, with first element as the new name, '
                    f'second element as the deprecated level: 0 as warning, 1 as exception'
                )
            if alias in kwargs:
                new_name, dep_level = new_arg
                if new_name in kwargs:
                    raise NotSupportedError(
                        f'{func_name} received both {alias} and {new_name}'
                    )

                if dep_level == 0:
                    warnings.warn(
                        f'`{alias}` is renamed to `{new_name}` in `{func_name}()`, the usage of `{alias}` is '
                        f'deprecated and will be removed in the next version.',
                        DeprecationWarning,
                    )
                    kwargs[new_name] = kwargs.pop(alias)
                elif dep_level == 1:
                    raise NotSupportedError(f'{alias} has been renamed to `{new_name}`')

    def deco(f):
        """
        Set Decorator function.

        :param f: function the decorator is used for
        :return: wrapper
        """

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            """
            Set wrapper function.
            :param args: wrapper arguments
            :param kwargs: wrapper key word arguments

            :return: result of renamed function.
            """
            _rename_kwargs(f.__name__, kwargs, aliases)
            return f(*args, **kwargs)

        return wrapper

    return deco


def deprecated_method(new_function_name):
    def deco(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f'`{func.__name__}` is renamed to `{new_function_name}`, the usage of `{func.__name__}` is '
                f'deprecated and will be removed.',
                DeprecationWarning,
            )
            return func(*args, **kwargs)

        return wrapper

    return deco


def retry(
    num_retry: int = 3,
    message: str = 'Calling {func_name} failed, retry attempt {attempt}/{num_retry}. Error: {error!r}',
):
    """
    Retry calling a function again in case of an error.

    :param num_retry: number of times to retry
    :param message: message to log when error happened
    :return: wrapper
    """
    from jina.logging.predefined import default_logger

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(num_retry):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    default_logger.warning(
                        message.format(
                            func_name=func.__name__,
                            attempt=i + 1,
                            num_retry=num_retry,
                            error=e,
                        )
                    )
                    if i + 1 == num_retry:
                        raise

        return wrapper

    return decorator


def get_readable_size(num_bytes: Union[int, float]) -> str:
    """
    Transform the bytes into readable value with different units (e.g. 1 KB, 20 MB, 30.1 GB).

    :param num_bytes: Number of bytes.
    :return: Human readable string representation.
    """
    num_bytes = int(num_bytes)
    if num_bytes < 1024:
        return f'{num_bytes} Bytes'
    elif num_bytes < 1024**2:
        return f'{num_bytes / 1024:.1f} KB'
    elif num_bytes < 1024**3:
        return f'{num_bytes / (1024 ** 2):.1f} MB'
    else:
        return f'{num_bytes / (1024 ** 3):.1f} GB'


def batch_iterator(
    data: Iterable[Any],
    batch_size: int,
    axis: int = 0,
) -> Iterator[Any]:
    """
    Get an iterator of batches of data.

    For example:
    .. highlight:: python
    .. code-block:: python

            for req in batch_iterator(data, batch_size, split_over_axis):
                pass  # Do something with batch

    :param data: Data source.
    :param batch_size: Size of one batch.
    :param axis: Determine which axis to iterate for np.ndarray data.
    :yield: data
    :return: An Iterator of batch data.
    """
    import numpy as np

    if not batch_size or batch_size <= 0:
        yield data
        return
    if isinstance(data, np.ndarray):
        _l = data.shape[axis]
        _d = data.ndim
        sl = [slice(None)] * _d
        if batch_size >= _l:
            yield data
            return
        for start in range(0, _l, batch_size):
            end = min(_l, start + batch_size)
            sl[axis] = slice(start, end)
            yield data[tuple(sl)]
    elif isinstance(data, Sequence):
        if batch_size >= len(data):
            yield data
            return
        for _ in range(0, len(data), batch_size):
            yield data[_ : _ + batch_size]
    elif isinstance(data, Iterable):
        # as iterator, there is no way to know the length of it
        iterator = iter(data)
        while True:
            chunk = tuple(islice(iterator, batch_size))
            if not chunk:
                return
            yield chunk
    else:
        raise TypeError(f'unsupported type: {type(data)}')


def parse_arg(v: str) -> Optional[Union[bool, int, str, list, float]]:
    """
    Parse the arguments from string to `Union[bool, int, str, list, float]`.

    :param v: The string of arguments
    :return: The parsed arguments list.
    """
    m = re.match(r'^[\'"](.*)[\'"]$', v)
    if m:
        return m.group(1)

    if v.startswith('[') and v.endswith(']'):
        # function args must be immutable tuples not list
        tmp = v.replace('[', '').replace(']', '').strip()
        if len(tmp) > 0:
            return [parse_arg(vv.strip()) for vv in tmp.split(',')]
        else:
            return []
    try:
        v = int(v)  # parse int parameter
    except ValueError:
        try:
            v = float(v)  # parse float parameter
        except ValueError:
            if len(v) == 0:
                # ignore it when the parameter is empty
                v = None
            elif v.lower() == 'true':  # parse boolean parameter
                v = True
            elif v.lower() == 'false':
                v = False
    return v


def countdown(t: int, reason: str = 'I am blocking this thread') -> None:
    """
    Display the countdown in console.

    For example:
        .. highlight:: python
        .. code-block:: python
            countdown(
                10, reason=colored('re-fetch access token', 'cyan', attrs=['bold', 'reverse'])
            )

    :param t: Countdown time.
    :param reason: A string message of reason for this Countdown.
    """
    try:
        sys.stdout.write('\n')
        sys.stdout.flush()
        while t > 0:
            t -= 1
            msg = f'⏳ {colored("%3d" % t, "yellow")}s left: {reason}'
            sys.stdout.write(f'\r{msg}')
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write('\n')
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write('no more patience? good bye!')


_random_names = (
    (
        'first',
        'great',
        'local',
        'small',
        'right',
        'large',
        'young',
        'early',
        'major',
        'clear',
        'black',
        'whole',
        'third',
        'white',
        'short',
        'human',
        'royal',
        'wrong',
        'legal',
        'final',
        'close',
        'total',
        'prime',
        'happy',
        'sorry',
        'basic',
        'aware',
        'ready',
        'green',
        'heavy',
        'extra',
        'civil',
        'chief',
        'usual',
        'front',
        'fresh',
        'joint',
        'alone',
        'rural',
        'light',
        'equal',
        'quiet',
        'quick',
        'daily',
        'urban',
        'upper',
        'moral',
        'vital',
        'empty',
        'brief',
    ),
    (
        'world',
        'house',
        'place',
        'group',
        'party',
        'money',
        'point',
        'state',
        'night',
        'water',
        'thing',
        'order',
        'power',
        'court',
        'level',
        'child',
        'south',
        'staff',
        'woman',
        'north',
        'sense',
        'death',
        'range',
        'table',
        'trade',
        'study',
        'other',
        'price',
        'class',
        'union',
        'value',
        'paper',
        'right',
        'voice',
        'stage',
        'light',
        'march',
        'board',
        'month',
        'music',
        'field',
        'award',
        'issue',
        'basis',
        'front',
        'heart',
        'force',
        'model',
        'space',
        'peter',
    ),
)


def random_name() -> str:
    """
    Generate a random name from list.

    :return: A Random name.
    """
    return '_'.join(random.choice(_random_names[j]) for j in range(2))


assigned_ports = set()
unassigned_ports = []
DEFAULT_MIN_PORT = 49153
MAX_PORT = 65535


def reset_ports():
    def _get_unassigned_ports():
        # if we are running out of ports, lower default minimum port
        if MAX_PORT - DEFAULT_MIN_PORT - len(assigned_ports) < 100:
            min_port = int(os.environ.get('JINA_RANDOM_PORT_MIN', '16384'))
        else:
            min_port = int(
                os.environ.get('JINA_RANDOM_PORT_MIN', str(DEFAULT_MIN_PORT))
            )
        max_port = int(os.environ.get('JINA_RANDOM_PORT_MAX', str(MAX_PORT)))
        return set(range(min_port, max_port + 1)) - set(assigned_ports)

    unassigned_ports.clear()
    assigned_ports.clear()
    unassigned_ports.extend(_get_unassigned_ports())
    random.shuffle(unassigned_ports)


def random_port() -> Optional[int]:
    """
    Get a random available port number.

    :return: A random port.
    """

    def _random_port():
        import socket

        def _check_bind(port):
            with socket.socket() as s:
                try:
                    s.bind(('', port))
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    return port
                except OSError:
                    return None

        _port = None
        if len(unassigned_ports) == 0:
            reset_ports()
        for idx, _port in enumerate(unassigned_ports):
            if _check_bind(_port) is not None:
                break
        else:
            raise OSError(
                f'can not find an available port in {len(unassigned_ports)} unassigned ports, assigned already {len(assigned_ports)} ports'
            )
        int_port = int(_port)
        unassigned_ports.pop(idx)
        assigned_ports.add(int_port)
        return int_port

    try:
        return _random_port()
    except OSError:
        assigned_ports.clear()
        unassigned_ports.clear()
        return _random_port()


def random_ports(n_ports):
    return [random_port() for _ in range(n_ports)]


def random_identity(use_uuid1: bool = False) -> str:
    """
    Generate random UUID.

    ..note::
        A MAC address or time-based ordering (UUID1) can afford increased database performance, since it's less work
        to sort numbers closer-together than those distributed randomly (UUID4) (see here).

        A second related issue, is that using UUID1 can be useful in debugging, even if origin data is lost or not
        explicitly stored.

    :param use_uuid1: use UUID1 instead of UUID4. This is the default Document ID generator.
    :return: A random UUID.

    """
    return random_uuid(use_uuid1).hex


def random_uuid(use_uuid1: bool = False) -> uuid.UUID:
    """
    Get a random UUID.

    :param use_uuid1: Use UUID1 if True, else use UUID4.
    :return: A random UUID.
    """
    return uuid.uuid1() if use_uuid1 else uuid.uuid4()


def expand_env_var(v: str) -> Optional[Union[bool, int, str, list, float]]:
    """
    Expand the environment variables.

    :param v: String of environment variables.
    :return: Parsed environment variables.
    """
    if isinstance(v, str):
        return parse_arg(os.path.expandvars(v))
    else:
        return v


def expand_dict(
    d: Dict, expand_fn=expand_env_var, resolve_cycle_ref=True
) -> Dict[str, Any]:
    """
    Expand variables from YAML file.

    :param d: Target Dict.
    :param expand_fn: Parsed environment variables.
    :param resolve_cycle_ref: Defines if cyclic references should be resolved.
    :return: Expanded variables.
    """
    expand_map = SimpleNamespace()
    pat = re.compile(r'{.+}|\$[a-zA-Z0-9_]*\b')

    def _scan(sub_d: Union[Dict, List], p):
        if isinstance(sub_d, dict):
            for k, v in sub_d.items():
                if isinstance(v, dict):
                    p.__dict__[k] = SimpleNamespace()
                    _scan(v, p.__dict__[k])
                elif isinstance(v, list):
                    p.__dict__[k] = list()
                    _scan(v, p.__dict__[k])
                else:
                    p.__dict__[k] = v
        elif isinstance(sub_d, list):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict):
                    p.append(SimpleNamespace())
                    _scan(v, p[idx])
                elif isinstance(v, list):
                    p.append(list())
                    _scan(v, p[idx])
                else:
                    p.append(v)

    def _replace(sub_d: Union[Dict, List], p):
        if isinstance(sub_d, Dict):
            for k, v in sub_d.items():
                if isinstance(v, (dict, list)):
                    _replace(v, p.__dict__[k])
                else:
                    if isinstance(v, str) and pat.findall(v):
                        sub_d[k] = _sub(v, p)
        elif isinstance(sub_d, List):
            for idx, v in enumerate(sub_d):
                if isinstance(v, (dict, list)):
                    _replace(v, p[idx])
                else:
                    if isinstance(v, str) and pat.findall(v):
                        sub_d[idx] = _sub(v, p)

    def _sub(v, p):
        if resolve_cycle_ref:
            try:
                v = v.format(root=expand_map, this=p)
            except KeyError:
                pass
        return expand_fn(v)

    _scan(d, expand_map)
    _replace(d, expand_map)
    return d


_ATTRIBUTES = {
    'bold': 1,
    'dark': 2,
    'underline': 4,
    'blink': 5,
    'reverse': 7,
    'concealed': 8,
}

_HIGHLIGHTS = {
    'on_grey': 40,
    'on_red': 41,
    'on_green': 42,
    'on_yellow': 43,
    'on_blue': 44,
    'on_magenta': 45,
    'on_cyan': 46,
    'on_white': 47,
}

_COLORS = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
}

_RESET = '\033[0m'

if __windows__:
    os.system('color')


def colored(
    text: str,
    color: Optional[str] = None,
    on_color: Optional[str] = None,
    attrs: Optional[Union[str, list]] = None,
) -> str:
    """
    Give the text with color.

    :param text: The target text.
    :param color: The color of text. Chosen from the following.
        {
            'grey': 30,
            'red': 31,
            'green': 32,
            'yellow': 33,
            'blue': 34,
            'magenta': 35,
            'cyan': 36,
            'white': 37
        }
    :param on_color: The on_color of text. Chosen from the following.
        {
            'on_grey': 40,
            'on_red': 41,
            'on_green': 42,
            'on_yellow': 43,
            'on_blue': 44,
            'on_magenta': 45,
            'on_cyan': 46,
            'on_white': 47
        }
    :param attrs: Attributes of color. Chosen from the following.
        {
           'bold': 1,
           'dark': 2,
           'underline': 4,
           'blink': 5,
           'reverse': 7,
           'concealed': 8
        }
    :return: Colored text.
    """
    if 'JINA_LOG_NO_COLOR' not in os.environ:
        fmt_str = '\033[%dm%s'
        if color:
            text = fmt_str % (_COLORS[color], text)
        if on_color:
            text = fmt_str % (_HIGHLIGHTS[on_color], text)

        if attrs:
            if isinstance(attrs, str):
                attrs = [attrs]
            if isinstance(attrs, list):
                for attr in attrs:
                    text = fmt_str % (_ATTRIBUTES[attr], text)
        text += _RESET
    return text


def colored_rich(
    text: str,
    color: Optional[str] = None,
    on_color: Optional[str] = None,
    attrs: Optional[Union[str, list]] = None,
) -> str:
    """
    Give the text with color. You should only use it when printing with rich print. Othersiwe please see the colored
    function

    :param text: The target text
    :param color: The color of text
    :param on_color: The on color of text: ex on yellow
    :param attrs: Attributes of color

    :return: Colored text.
    """
    if 'JINA_LOG_NO_COLOR' not in os.environ:
        if color:
            text = _wrap_text_in_rich_bracket(text, color)
        if on_color:
            text = _wrap_text_in_rich_bracket(text, on_color)

        if attrs:
            if isinstance(attrs, str):
                attrs = [attrs]
            if isinstance(attrs, list):
                for attr in attrs:
                    text = _wrap_text_in_rich_bracket(text, attr)
    return text


def _wrap_text_in_rich_bracket(text: str, wrapper: str):
    return f'[{wrapper}]{text}[/{wrapper}]'


def warn_unknown_args(unknown_args: List[str]):
    """Creates warnings for all given arguments.

    :param unknown_args: arguments that are possibly unknown to Jina
    """

    from jina_cli.lookup import _build_lookup_table

    all_args = _build_lookup_table()[0]
    has_migration_tip = False
    real_unknown_args = []
    warn_strs = []
    for arg in unknown_args:
        if arg.replace('--', '') not in all_args:
            from jina.parsers.deprecated import get_deprecated_replacement

            new_arg = get_deprecated_replacement(arg)
            if new_arg:
                if not has_migration_tip:
                    warn_strs.append('Migration tips:')
                    has_migration_tip = True
                warn_strs.append(f'\t`{arg}` has been renamed to `{new_arg}`')
            real_unknown_args.append(arg)

    if real_unknown_args:
        warn_strs = [f'ignored unknown argument: {real_unknown_args}.'] + warn_strs
        warnings.warn(''.join(warn_strs))


class ArgNamespace:
    """Helper function for argparse.Namespace object."""

    @staticmethod
    def kwargs2list(kwargs: Dict) -> List[str]:
        """
        Convert dict to an argparse-friendly list.

        :param kwargs: dictionary of key-values to be converted
        :return: argument list
        """
        args = []
        from jina.serve.executors import BaseExecutor
        from jina.serve.gateway import BaseGateway

        for k, v in kwargs.items():
            k = k.replace('_', '-')
            if v is not None:
                if isinstance(v, bool):
                    if v:
                        args.append(f'--{k}')
                elif isinstance(v, list):  # for nargs
                    args.extend([f'--{k}', *(str(vv) for vv in v)])
                elif isinstance(v, dict):
                    args.extend([f'--{k}', json.dumps(v)])
                elif isinstance(v, type) and issubclass(v, BaseExecutor):
                    args.extend([f'--{k}', v.__name__])
                elif isinstance(v, type) and issubclass(v, BaseGateway):
                    args.extend([f'--{k}', v.__name__])
                else:
                    args.extend([f'--{k}', str(v)])
        return args

    @staticmethod
    def kwargs2namespace(
        kwargs: Dict[str, Union[str, int, bool]],
        parser: ArgumentParser,
        warn_unknown: bool = False,
        fallback_parsers: Optional[List[ArgumentParser]] = None,
        positional_args: Optional[Tuple[str, ...]] = None,
    ) -> Namespace:
        """
        Convert dict to a namespace.

        :param kwargs: dictionary of key-values to be converted
        :param parser: the parser for building kwargs into a namespace
        :param warn_unknown: True, if unknown arguments should be logged
        :param fallback_parsers: a list of parsers to help resolving the args
        :param positional_args: some parser requires positional arguments to be presented
        :return: argument list
        """
        args = ArgNamespace.kwargs2list(kwargs)
        if positional_args:
            args += positional_args
        p_args, unknown_args = parser.parse_known_args(args)
        unknown_args = list(filter(lambda x: x.startswith('--'), unknown_args))
        if '--jcloud' in unknown_args:
            unknown_args.remove('--jcloud')
        if warn_unknown and unknown_args:
            _leftovers = set(unknown_args)
            if fallback_parsers:
                for p in fallback_parsers:
                    _, _unk_args = p.parse_known_args(args)
                    _leftovers = _leftovers.intersection(_unk_args)
                    if not _leftovers:
                        # all args have been resolved
                        break
            warn_unknown_args(_leftovers)

        return p_args

    @staticmethod
    def get_non_defaults_args(
        args: Namespace, parser: ArgumentParser, taboo: Optional[Set[str]] = None
    ) -> Dict:
        """
        Get non-default args in a dict.

        :param args: the namespace to parse
        :param parser: the parser for referring the default values
        :param taboo: exclude keys in the final result
        :return: non defaults
        """
        if taboo is None:
            taboo = set()
        non_defaults = {}
        _defaults = vars(parser.parse_args([]))
        for k, v in vars(args).items():
            if k in _defaults and k not in taboo and _defaults[k] != v:
                non_defaults[k] = v
        return non_defaults

    @staticmethod
    def flatten_to_dict(
        args: Union[Dict[str, 'Namespace'], 'Namespace']
    ) -> Dict[str, Any]:
        """Convert argparse.Namespace to dict to be uploaded via REST.

        :param args: namespace or dict or namespace to dict.
        :return: pod args
        """
        if isinstance(args, Namespace):
            return vars(args)
        elif isinstance(args, dict):
            pod_args = {}
            for k, v in args.items():
                if isinstance(v, Namespace):
                    pod_args[k] = vars(v)
                elif isinstance(v, list):
                    pod_args[k] = [vars(_) for _ in v]
                else:
                    pod_args[k] = v
            return pod_args


def is_valid_local_config_source(path: str) -> bool:
    # TODO: this function must be refactored before 1.0 (Han 12.22)
    """
    Check if the path is valid.

    :param path: Local file path.
    :return: True if the path is valid else False.
    """
    try:
        from jina.jaml import parse_config_source

        parse_config_source(path)
        return True
    except FileNotFoundError:
        return False


def get_full_version() -> Optional[Tuple[Dict, Dict]]:
    """
    Get the version of libraries used in Jina and environment variables.

    :return: Version information and environment variables
    """
    import os
    import platform
    from uuid import getnode

    import google.protobuf
    import grpc
    import yaml
    from google.protobuf.internal import api_implementation
    from grpc import _grpcio_metadata

    try:
        from hubble import __version__ as __hubble_version__
    except:
        __hubble_version__ = 'not-available'
    try:
        from jcloud import __version__ as __jcloud_version__
    except:
        __jcloud_version__ = 'not-available'

    from jina import (
        __docarray_version__,
        __jina_env__,
        __proto_version__,
        __unset_msg__,
        __uptime__,
        __version__,
    )
    from jina.logging.predefined import default_logger

    try:

        info = {
            'jina': __version__,
            'docarray': __docarray_version__,
            'jcloud': __jcloud_version__,
            'jina-hubble-sdk': __hubble_version__,
            'jina-proto': __proto_version__,
            'protobuf': google.protobuf.__version__,
            'proto-backend': api_implementation.Type(),
            'grpcio': getattr(grpc, '__version__', _grpcio_metadata.__version__),
            'pyyaml': yaml.__version__,
            'python': platform.python_version(),
            'platform': platform.system(),
            'platform-release': platform.release(),
            'platform-version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'uid': getnode(),
            'session-id': str(random_uuid(use_uuid1=True)),
            'uptime': __uptime__,
            'ci-vendor': get_ci_vendor() or __unset_msg__,
            'internal': 'jina-ai'
            in os.getenv('GITHUB_ACTION_REPOSITORY', __unset_msg__),
        }

        env_info = {k: os.getenv(k, __unset_msg__) for k in __jina_env__}
        full_version = info, env_info
    except Exception as e:
        default_logger.error(str(e))
        full_version = None

    return full_version


def format_full_version_info(info: Dict, env_info: Dict) -> str:
    """
    Format the version information.

    :param info: Version information of Jina libraries.
    :param env_info: The Jina environment variables.
    :return: Formatted version information.
    """
    version_info = '\n'.join(f'- {k:30s}{v}' for k, v in info.items())
    env_info = '\n'.join(f'* {k:30s}{v}' for k, v in env_info.items())
    return version_info + '\n' + env_info


def _update_policy():
    if __windows__:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    elif 'JINA_DISABLE_UVLOOP' in os.environ:
        return
    else:
        try:
            import uvloop

            if not isinstance(asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy):
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except ModuleNotFoundError:
            warnings.warn(
                'Install `uvloop` via `pip install "jina[uvloop]"` for better performance.'
            )


def get_or_reuse_loop():
    """
    Get a new eventloop or reuse the current opened eventloop.

    :return: A new eventloop or reuse the current opened eventloop.
    """
    _update_policy()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        # no event loop
        # create a new loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def typename(obj):
    """
    Get the typename of object.

    :param obj: Target object.
    :return: Typename of the obj.
    """
    if not isinstance(obj, type):
        obj = obj.__class__
    try:
        return f'{obj.__module__}.{obj.__name__}'
    except AttributeError:
        return str(obj)


class CatchAllCleanupContextManager:
    """
    This context manager guarantees, that the :method:``__exit__`` of the
    sub context is called, even when there is an Exception in the
    :method:``__enter__``.

    :param sub_context: The context, that should be taken care of.
    """

    def __init__(self, sub_context):
        self.sub_context = sub_context

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.sub_context.__exit__(exc_type, exc_val, exc_tb)


class cached_property:
    """The decorator to cache property of a class."""

    def __init__(self, func):
        """
        Create the :class:`cached_property`.

        :param func: Cached function.
        """
        self.func = func

    def __get__(self, obj, cls):
        cached_value = obj.__dict__.get(f'CACHED_{self.func.__name__}', None)
        if cached_value is not None:
            return cached_value

        value = obj.__dict__[f'CACHED_{self.func.__name__}'] = self.func(obj)
        return value

    def __delete__(self, obj):
        cached_value = obj.__dict__.get(f'CACHED_{self.func.__name__}', None)
        if cached_value is not None:
            if hasattr(cached_value, 'close'):
                cached_value.close()
            del obj.__dict__[f'CACHED_{self.func.__name__}']


class _cache_invalidate:
    """Class for cache invalidation, remove strategy.

    :param func: func to wrap as a decorator.
    :param attribute: String as the function name to invalidate cached
        data. E.g. in :class:`cached_property` we cache data inside the class obj
        with the `key`: `CACHED_{func.__name__}`, the func name in `cached_property`
        is the name to invalidate.
    """

    def __init__(self, func, attribute: str):
        self.func = func
        self.attribute = attribute

    def __call__(self, *args, **kwargs):
        obj = args[0]
        cached_key = f'CACHED_{self.attribute}'
        if cached_key in obj.__dict__:
            del obj.__dict__[cached_key]  # invalidate
        self.func(*args, **kwargs)

    def __get__(self, obj, cls):
        from functools import partial

        return partial(self.__call__, obj)


def cache_invalidate(attribute: str):
    """The cache invalidator decorator to wrap the method call.

    Check the implementation in :class:`_cache_invalidate`.

    :param attribute: The func name as was stored in the obj to invalidate.
    :return: wrapped method.
    """

    def _wrap(func):
        return _cache_invalidate(func, attribute)

    return _wrap


def get_now_timestamp():
    """
    Get the datetime.

    :return: The datetime in int format.
    """
    now = datetime.now()
    return int(datetime.timestamp(now))


def get_readable_time(*args, **kwargs):
    """
    Get the datetime in human readable format (e.g. 115 days and 17 hours and 46 minutes and 40 seconds).

    For example:
        .. highlight:: python
        .. code-block:: python
            get_readable_time(seconds=1000)

    :param args: arguments for datetime.timedelta
    :param kwargs: key word arguments for datetime.timedelta
    :return: Datetime in human readable format.
    """
    import datetime

    secs = float(datetime.timedelta(*args, **kwargs).total_seconds())
    units = [('day', 86400), ('hour', 3600), ('minute', 60), ('second', 1)]
    parts = []
    for unit, mul in units:
        if secs / mul >= 1 or mul == 1:
            if mul > 1:
                n = int(math.floor(secs / mul))
                secs -= n * mul
            else:
                n = int(secs)
            parts.append(f'{n} {unit}' + ('' if n == 1 else 's'))
    return ' and '.join(parts)


def get_internal_ip():
    """
    Return the private IP address of the gateway for connecting from other machine in the same network.

    :return: Private IP address.
    """
    import socket

    ip = '127.0.0.1'
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
    except Exception:
        pass
    return ip


def get_public_ip(timeout: float = 0.3):
    """
    Return the public IP address of the gateway for connecting from other machine in the public network.

    :param timeout: the seconds to wait until return None.

    :return: Public IP address.

    .. warn::
        Set `timeout` to a large number will block the Flow.

    """
    import urllib.request

    results = []

    def _get_ip(url):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout) as fp:
                _ip = fp.read().decode().strip()
                results.append(_ip)

        except:
            pass  # intentionally ignored, public ip is not showed

    ip_server_list = [
        'https://api.ipify.org',
        'https://ident.me',
        'https://checkip.amazonaws.com/',
    ]

    threads = []

    for idx, ip in enumerate(ip_server_list):
        t = threading.Thread(target=_get_ip, args=(ip,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout)

    for r in results:
        if r:
            return r


def convert_tuple_to_list(d: Dict):
    """
    Convert all the tuple type values from a dict to list.

    :param d: Dict type of data.
    """
    for k, v in d.items():
        if isinstance(v, tuple):
            d[k] = list(v)
        elif isinstance(v, dict):
            convert_tuple_to_list(v)


def is_jupyter() -> bool:  # pragma: no cover
    """
    Check if we're running in a Jupyter notebook, using magic command `get_ipython` that only available in Jupyter.

    :return: True if run in a Jupyter notebook else False.
    """
    try:
        get_ipython  # noqa: F821
    except NameError:
        return False
    shell = get_ipython().__class__.__name__  # noqa: F821
    if shell == 'ZMQInteractiveShell':
        return True  # Jupyter notebook or qtconsole
    elif shell == 'Shell':
        return True  # Google colab
    elif shell == 'TerminalInteractiveShell':
        return False  # Terminal running IPython
    else:
        return False  # Other type (?)


def iscoroutinefunction(func: Callable):
    return inspect.iscoroutinefunction(func)


def run_async(func, *args, **kwargs):
    """Generalized asyncio.run for jupyter notebook.

    When running inside jupyter, an eventloop already exists, can't be stopped, can't be killed.
    Directly calling asyncio.run will fail, as This function cannot be called when another asyncio event loop
    is running in the same thread.

    .. see_also:
        https://stackoverflow.com/questions/55409641/asyncio-run-cannot-be-called-from-a-running-event-loop

    :param func: function to run
    :param args: parameters
    :param kwargs: key-value parameters
    :return: asyncio.run(func)
    """

    class _RunThread(threading.Thread):
        """Create a running thread when in Jupyter notebook."""

        def run(self):
            """Run given `func` asynchronously."""
            self.result = asyncio.run(func(*args, **kwargs))

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # eventloop already exist
        # running inside Jupyter
        if is_jupyter():
            thread = _RunThread()
            thread.start()
            thread.join()
            try:
                return thread.result
            except AttributeError:
                from jina.excepts import BadClient

                raise BadClient(
                    'something wrong when running the eventloop, result can not be retrieved'
                )
        else:

            raise RuntimeError(
                'you have an eventloop running but not using Jupyter/ipython, '
                'this may mean you are using Jina with other integration? if so, then you '
                'may want to use Client/Flow(asyncio=True). If not, then '
                'please report this issue here: https://github.com/jina-ai/jina'
            )
    else:
        return asyncio.run(func(*args, **kwargs))


def slugify(value):
    """
    Normalize string, converts to lowercase, removes non-alpha characters, and converts spaces to hyphens.

    :param value: Original string.
    :return: Processed string.
    """
    s = str(value).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def is_yaml_filepath(val) -> bool:
    """
    Check if the file is YAML file.

    :param val: Path of target file.
    :return: True if the file is YAML else False.
    """
    if __windows__:
        r = r'.*.ya?ml$'  # TODO: might not be exhaustive
    else:
        r = r'^[/\w\-\_\.]+.ya?ml$'
    return re.match(r, val.strip()) is not None


def download_mermaid_url(mermaid_url, output) -> None:
    """
    Download the jpg image from mermaid_url.

    :param mermaid_url: The URL of the image.
    :param output: A filename specifying the name of the image to be created, the suffix svg/jpg determines the file type of the output image.
    """
    from urllib.request import Request, urlopen

    try:
        req = Request(mermaid_url, headers={'User-Agent': 'Mozilla/5.0'})
        with open(output, 'wb') as fp:
            fp.write(urlopen(req).read())
    except:
        from jina.logging.predefined import default_logger

        default_logger.error(
            'can not download image, please check your graph and the network connections'
        )


def find_request_binding(target):
    """Find `@request` decorated methods in a class.

    :param target: the target class to check
    :return: a dictionary with key as request type and value as method name
    """
    import ast
    import inspect

    from jina import __default_endpoint__

    res = {}

    def visit_function_def(node):

        for e in node.decorator_list:
            req_name = ''
            if isinstance(e, ast.Call) and e.func.id == 'requests':
                req_name = e.keywords[0].value.s
            elif isinstance(e, ast.Name) and e.id == 'requests':
                req_name = __default_endpoint__
            if req_name:
                if req_name in res:
                    raise ValueError(
                        f'you already bind `{res[req_name]}` with `{req_name}` request'
                    )
                else:
                    res[req_name] = node.name

    V = ast.NodeVisitor()
    V.visit_FunctionDef = visit_function_def
    V.visit(compile(inspect.getsource(target), '?', 'exec', ast.PyCF_ONLY_AST))
    return res


def dunder_get(_dict: Any, key: str) -> Any:
    """Returns value for a specified dunderkey
    A "dunderkey" is just a fieldname that may or may not contain
    double underscores (dunderscores!) for referencing nested keys in
    a dict. eg::
         >>> data = {'a': {'b': 1}}
         >>> dunder_get(data, 'a__b')
         1
    key 'b' can be referrenced as 'a__b'
    :param _dict : (dict, list, struct or object) which we want to index into
    :param key   : (str) that represents a first level or nested key in the dict
    :return: (mixed) value corresponding to the key
    """

    try:
        part1, part2 = key.split('__', 1)
    except ValueError:
        part1, part2 = key, ''

    try:
        part1 = int(part1)  # parse int parameter
    except ValueError:
        pass

    from google.protobuf.struct_pb2 import ListValue, Struct

    if isinstance(part1, int):
        result = _dict[part1]
    elif isinstance(_dict, (dict, Struct, MutableMapping)):
        if part1 in _dict:
            result = _dict[part1]
        else:
            result = None
    elif isinstance(_dict, (Iterable, ListValue)):
        result = _dict[part1]
    else:
        result = getattr(_dict, part1)

    return dunder_get(result, part2) if part2 else result


if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI


def extend_rest_interface(app: 'FastAPI') -> 'FastAPI':
    """Extend Jina built-in FastAPI instance with customized APIs, routing, etc.

    :param app: the built-in FastAPI instance given by Jina
    :return: the extended FastAPI instance

    .. highlight:: python
    .. code-block:: python

        def extend_rest_interface(app: 'FastAPI'):
            @app.get('/extension1')
            async def root():
                return {"message": "Hello World"}

            return app
    """
    return app


def get_ci_vendor() -> Optional[str]:
    from jina import __resources_path__

    with open(os.path.join(__resources_path__, 'ci-vendors.json')) as fp:
        all_cis = json.load(fp)
        for c in all_cis:
            if isinstance(c['env'], str) and c['env'] in os.environ:
                return c['constant']
            elif isinstance(c['env'], dict):
                for k, v in c['env'].items():
                    if os.environ.get(k, None) == v:
                        return c['constant']
            elif isinstance(c['env'], list):
                for k in c['env']:
                    if k in os.environ:
                        return c['constant']


def deprecate_by(new_fn):
    def _f(*args, **kwargs):
        import inspect

        old_fn_name = inspect.stack()[1][4][0].strip().split("=")[0].strip()
        warnings.warn(
            f'`{old_fn_name}` is renamed to `{new_fn.__name__}` with the same usage, please use the latter instead. '
            f'The old function will be removed soon.',
            DeprecationWarning,
        )
        return new_fn(*args, **kwargs)

    return _f


def get_request_header() -> Dict:
    """Return the header of request.

    :return: request header
    """
    metas, envs = get_full_version()

    header = {
        **{f'jinameta-{k}': str(v) for k, v in metas.items()},
        **envs,
    }
    return header


def get_rich_console():
    """
    Function to get jina rich default console.
    :return: rich console
    """
    return Console(
        force_terminal=True if 'PYCHARM_HOSTED' in os.environ else None,
        color_system=None if 'JINA_LOG_NO_COLOR' in os.environ else 'auto',
    )


from jina.parsers import set_client_cli_parser

__default_port_client__ = 80
__default_port_tls_client__ = 443


def parse_client(kwargs) -> Namespace:
    """
    Parse the kwargs for the Client

    :param kwargs: kwargs to be parsed

    :return: parsed argument.
    """
    kwargs = _parse_kwargs(kwargs)
    args = ArgNamespace.kwargs2namespace(
        kwargs, set_client_cli_parser(), warn_unknown=True
    )

    if not args.port:
        args.port = (
            __default_port_client__ if not args.tls else __default_port_tls_client__
        )

    return args


def _parse_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if 'host' in kwargs.keys():
        return_scheme = dict()
        (
            kwargs['host'],
            return_scheme['port'],
            return_scheme['protocol'],
            return_scheme['tls'],
        ) = parse_host_scheme(kwargs['host'])

        for key, value in return_scheme.items():
            if value:
                if key in kwargs:
                    raise ValueError(
                        f"You can't have two definitions of {key}: you have one in the host scheme and one in the keyword argument"
                    )
                elif value:
                    kwargs[key] = value

    kwargs = _delete_host_slash(kwargs)

    return kwargs


def _delete_host_slash(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if 'host' in kwargs:
        if kwargs['host'][-1] == '/':
            kwargs['host'] = kwargs['host'][:-1]
    return kwargs


def parse_host_scheme(host: str) -> Tuple[str, str, str, bool]:
    scheme, _hostname, port = _parse_url(host)

    tls = None
    if scheme in ('grpcs', 'https', 'wss'):
        scheme = scheme[:-1]
        tls = True

    if scheme == 'ws':
        scheme = 'websocket'

    return _hostname, port, scheme, tls


def _parse_url(host):
    if '://' in host:
        scheme, host = host.split('://')
    else:
        scheme = None

    if ':' in host:
        host, port = host.split(':')
    else:
        port = None

    return scheme, host, port


def _single_port_free(host: str, port: int) -> bool:
    with socket(AF_INET, SOCK_STREAM) as session:
        if session.connect_ex((host, port)) == 0:
            return False
        else:
            return True


def is_port_free(host: Union[str, List[str]], port: Union[int, List[int]]) -> bool:
    if isinstance(port, list):
        if isinstance(host, str):
            return all([_single_port_free(host, _p) for _p in port])
        else:
            return all([all([_single_port_free(_h, _p) for _p in port]) for _h in host])
    else:
        if isinstance(host, str):
            return _single_port_free(host, port)
        else:
            return all([_single_port_free(_h, port) for _h in host])
    

def send_telemetry_event(event: str, obj: Any, **kwargs) -> None:
    """Sends in a thread a request with telemetry for a given event
    :param event: Event leading to the telemetry entry
    :param obj: Object to be tracked
    :param kwargs: Extra kwargs to be passed to the data sent
    """

    if 'JINA_OPTOUT_TELEMETRY' in os.environ:
        return

    def _telemetry():
        url = 'https://telemetry.jina.ai/'
        try:
            from jina.helper import get_full_version

            metas, _ = get_full_version()
            data = base64.urlsafe_b64encode(
                json.dumps(
                    {**metas, 'event': f'{obj.__class__.__name__}.{event}', **kwargs}
                ).encode('utf-8')
            )

            req = urllib.request.Request(
                url, data=data, headers={'User-Agent': 'Mozilla/5.0'}
            )
            urllib.request.urlopen(req)

        except:
            pass

    threading.Thread(target=_telemetry, daemon=True).start()

