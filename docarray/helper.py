import os
import random
import sys
import uuid
import warnings
from typing import TypeVar, Iterable, Any, Dict, Optional

T = TypeVar('T')

__windows__ = sys.platform == 'win32'

__resources_path__ = os.path.join(
    os.path.dirname(
        sys.modules.get('docarray').__file__ if 'docarray' in sys.modules else __file__
    ),
    'resources',
)


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


def deprecate_by(new_fn):
    """A helper function to label deprecated function

    Usage: old_fn_name = deprecate_by(new_fn)

    :param new_fn: the new function
    :return: a wrapped function with old function name
    """

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

    from google.protobuf.struct_pb2 import ListValue
    from google.protobuf.struct_pb2 import Struct
    from google.protobuf.pyext._message import MessageMapContainer
    from .simple.struct import StructView

    if isinstance(part1, int):
        result = _dict[part1]
    elif isinstance(_dict, (dict, Struct, MessageMapContainer, StructView)):
        if part1 in _dict:
            result = _dict[part1]
        else:
            result = None
    elif isinstance(_dict, (Iterable, ListValue)):
        result = _dict[part1]
    else:
        result = getattr(_dict, part1)

    return dunder_get(result, part2) if part2 else result


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
        raise RuntimeError('Invalid or too-complicated graph')


def get_request_header() -> Dict:
    """Return the header of request.

    :return: request header
    """
    return {k: str(v) for k, v in get_full_version().items()}


def get_full_version() -> Dict:
    """
    Get the version of libraries used in Jina and environment variables.

    :return: Version information and environment variables
    """
    import google.protobuf, platform
    from . import __version__
    from google.protobuf.internal import api_implementation
    from uuid import getnode

    return {
        'docarray': __version__,
        'protobuf': google.protobuf.__version__,
        'proto-backend': api_implementation._default_implementation_type,
        'python': platform.python_version(),
        'platform': platform.system(),
        'platform-release': platform.release(),
        'platform-version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'uid': getnode(),
        'session-id': str(random_uuid(use_uuid1=True)),
    }


def random_port() -> Optional[int]:
    """
    Get a random available port number from '49153' to '65535'.

    :return: A random port.
    """

    import threading
    import multiprocessing
    from contextlib import closing
    import socket

    def _get_port(port=0):
        with multiprocessing.Lock():
            with threading.Lock():
                with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                    try:
                        s.bind(('', port))
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        return s.getsockname()[1]
                    except OSError:
                        pass

    _port = None
    if 'JINA_RANDOM_PORT_MIN' in os.environ or 'JINA_RANDOM_PORT_MAX' in os.environ:
        min_port = int(os.environ.get('JINA_RANDOM_PORT_MIN', '49153'))
        max_port = int(os.environ.get('JINA_RANDOM_PORT_MAX', '65535'))
        all_ports = list(range(min_port, max_port + 1))
        random.shuffle(all_ports)
        for _port in all_ports:
            if _get_port(_port) is not None:
                break
        else:
            raise OSError(
                f'can not find an available port between [{min_port}, {max_port}].'
            )
    else:
        _port = _get_port()

    return int(_port)
