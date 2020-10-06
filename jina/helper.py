__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import functools
import math
import os
import random
import re
import sys
import time
from argparse import ArgumentParser, Namespace
from datetime import datetime
from io import StringIO
from itertools import islice
from types import SimpleNamespace, ModuleType
from typing import Tuple, Optional, Iterator, Any, Union, List, Dict, Set, TextIO, Sequence, Iterable

from ruamel.yaml import YAML, nodes

if False:
    from uvloop import Loop

__all__ = ['batch_iterator', 'yaml',
           'load_contrib_module',
           'parse_arg',
           'PathImporter', 'random_port', 'get_random_identity', 'expand_env_var',
           'colored', 'kwargs2list', 'get_local_config_source', 'is_valid_local_config_source',
           'cached_property', 'is_url', 'complete_path']


def deprecated_alias(**aliases):
    def deco(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            rename_kwargs(f.__name__, kwargs, aliases)
            return f(*args, **kwargs)

        return wrapper

    return deco


def rename_kwargs(func_name: str, kwargs, aliases):
    from .logging import default_logger
    for alias, new in aliases.items():
        if alias in kwargs:
            if new in kwargs:
                raise TypeError(f'{func_name} received both {alias} and {new}')
            default_logger.warning(
                f'"{alias}" is deprecated in "{func_name}()" '
                f'and will be removed in the next version; please use "{new}" instead')
            kwargs[new] = kwargs.pop(alias)


def get_readable_size(num_bytes: Union[int, float]) -> str:
    num_bytes = int(num_bytes)
    if num_bytes < 1024:
        return f'{num_bytes} Bytes'
    elif num_bytes < 1024 ** 2:
        return f'{num_bytes / 1024:.1f} KB'
    elif num_bytes < 1024 ** 3:
        return f'{num_bytes / (1024 ** 2):.1f} MB'
    else:
        return f'{num_bytes / (1024 ** 3):.1f} GB'


def print_load_table(load_stat: Dict[str, List[Any]]):
    from .logging import default_logger

    load_table = []
    cached = set()

    for k, v in load_stat.items():
        for cls_name, import_stat, err_reason in v:
            if cls_name not in cached:
                load_table.append('%-5s %-25s %-40s %s' % (
                    colored('✓', 'green') if import_stat else colored('✗', 'red'),
                    cls_name if cls_name else colored('Module load error', 'red'), k, str(err_reason)))
                cached.add(cls_name)
    if load_table:
        load_table.sort()
        load_table = ['', '%-5s %-25s %-40s %-s' % ('Load', 'Class', 'Module', 'Dependency'),
                      '%-5s %-25s %-40s %-s' % ('-' * 5, '-' * 25, '-' * 40, '-' * 10)] + load_table
        default_logger.info('\n'.join(load_table))


def print_load_csv_table(load_stat: Dict[str, List[Any]]):
    from .logging import default_logger

    load_table = []
    for k, v in load_stat.items():
        for cls_name, import_stat, err_reason in v:
            load_table.append('%s %s %s %s' % (
                colored('✓', 'green') if import_stat else colored('✗', 'red'),
                cls_name if cls_name else colored('Module_load_error', 'red'), k, str(err_reason)))
    if load_table:
        default_logger.info('\n'.join(load_table))


def print_dep_tree_rst(fp, dep_tree, title='Executor'):
    tableview = set()
    treeview = []

    def _iter(d, depth):
        for k, v in d.items():
            if k != 'module':
                treeview.append('   ' * depth + f'- `{k}`')
                tableview.add(f'| `{k}` | ' + (f'`{d["module"]}`' if 'module' in d else ' ') + ' |')
                _iter(v, depth + 1)

    _iter(dep_tree, 0)

    fp.write(f'# List of {len(tableview)} {title}s in Jina\n\n'
             f'This version of Jina includes {len(tableview)} {title}s.\n\n'
             f'## Inheritances in a Tree View\n')
    fp.write('\n'.join(treeview))

    fp.write(f'\n\n## Modules in a Table View \n\n| Class | Module |\n')
    fp.write('| --- | --- |\n')
    fp.write('\n'.join(sorted(tableview)))


def call_obj_fn(obj, fn: str):
    if obj is not None and hasattr(obj, fn):
        getattr(obj, fn)()


def touch_dir(base_dir: str) -> None:
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)


def batch_iterator(data: Iterable[Any], batch_size: int, axis: int = 0,
                   yield_slice: bool = False) -> Iterator[Any]:
    import numpy as np
    if not batch_size or batch_size <= 0:
        yield data
        return
    if isinstance(data, np.ndarray):
        _l = data.shape[axis]
        _d = data.ndim
        sl = [slice(None)] * _d
        if batch_size >= _l:
            if yield_slice:
                yield tuple(sl)
            else:
                yield data
            return
        for start in range(0, _l, batch_size):
            end = min(_l, start + batch_size)
            sl[axis] = slice(start, end)
            if yield_slice:
                yield tuple(sl)
            else:
                yield data[tuple(sl)]
    elif isinstance(data, Sequence):
        if batch_size >= len(data):
            yield data
            return
        for _ in range(0, len(data), batch_size):
            yield data[_:_ + batch_size]
    elif isinstance(data, Iterable):
        data = iter(data)
        # as iterator, there is no way to know the length of it
        while True:
            chunk = tuple(islice(data, batch_size))
            if not chunk:
                return
            yield chunk
    else:
        raise TypeError(f'unsupported type: {type(data)}')


def _get_yaml():
    y = YAML(typ='safe')
    y.default_flow_style = False
    return y


def parse_arg(v: str) -> Optional[Union[bool, int, str, list, float]]:
    if v.startswith('[') and v.endswith(']'):
        # function args must be immutable tuples not list
        tmp = v.replace('[', '').replace(']', '').strip().split(',')
        if len(tmp) > 0:
            return [parse_arg(vv.strip()) for vv in tmp]
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


def load_contrib_module() -> Optional[List[Any]]:
    if 'JINA_CONTRIB_MODULE_IS_LOADING' not in os.environ:

        contrib = os.getenv('JINA_CONTRIB_MODULE')
        os.environ['JINA_CONTRIB_MODULE_IS_LOADING'] = 'true'

        modules = []

        if contrib:
            from .logging import default_logger
            default_logger.info(
                f'find a value in $JINA_CONTRIB_MODULE={contrib}, will load them as external modules')
            for p in contrib.split(','):
                m = PathImporter.add_modules(p)
                modules.append(m)
                default_logger.info(f'successfully registered {m} class, you can now use it via yaml.')
    else:
        modules = None

    return modules


class PathImporter:

    @staticmethod
    def _get_module_name(path: str, use_abspath: bool = False, use_basename: bool = True) -> str:
        module_name = os.path.dirname(os.path.abspath(path) if use_abspath else path)
        if use_basename:
            module_name = os.path.basename(module_name)
        module_name = module_name.replace('/', '.').strip('.')
        return module_name

    @staticmethod
    def add_modules(*paths) -> Optional[ModuleType]:
        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError('cannot import module from %s, file not exist', p)
            module = PathImporter._path_import(p)
        return module

    @staticmethod
    def _path_import(absolute_path: str) -> Optional[ModuleType]:
        import importlib.util
        try:
            # module_name = (PathImporter._get_module_name(absolute_path) or
            #                PathImporter._get_module_name(absolute_path, use_abspath=True) or 'jinahub')

            # I dont want to trust user path based on directory structure, "jinahub", period
            spec = importlib.util.spec_from_file_location('jinahub', absolute_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module  # add this line
            spec.loader.exec_module(module)
        except ModuleNotFoundError:
            module = None
        return module


_random_names = (('first', 'great', 'local', 'small', 'right', 'large', 'young', 'early', 'major', 'clear', 'black',
                  'whole', 'third', 'white', 'short', 'human', 'royal', 'wrong', 'legal', 'final', 'close', 'total',
                  'prime', 'happy', 'sorry', 'basic', 'aware', 'ready', 'green', 'heavy', 'extra', 'civil', 'chief',
                  'usual', 'front', 'fresh', 'joint', 'alone', 'rural', 'light', 'equal', 'quiet', 'quick', 'daily',
                  'urban', 'upper', 'moral', 'vital', 'empty', 'brief',),
                 ('world', 'house', 'place', 'group', 'party', 'money', 'point', 'state', 'night', 'water', 'thing',
                  'order', 'power', 'court', 'level', 'child', 'south', 'staff', 'woman', 'north', 'sense', 'death',
                  'range', 'table', 'trade', 'study', 'other', 'price', 'class', 'union', 'value', 'paper', 'right',
                  'voice', 'stage', 'light', 'march', 'board', 'month', 'music', 'field', 'award', 'issue', 'basis',
                  'front', 'heart', 'force', 'model', 'space', 'peter',))


def random_name() -> str:
    return '_'.join(random.choice(_random_names[j]) for j in range(2))


def random_port() -> Optional[int]:
    import threading
    from contextlib import closing
    import socket

    def _get_port(port=0):
        with threading.Lock():
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.bind(('', port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return s.getsockname()[1]

    _port = None
    if 'JINA_RANDOM_PORTS' in os.environ:
        min_port, max_port = 49152, 65535
        while True:
            _port = random.randrange(min_port, max_port)
            if _get_port(_port) is not None:
                break
    else:
        _port = _get_port()
    return _port


def get_random_identity() -> str:
    return f'{random.getrandbits(40):010x}'


yaml = _get_yaml()


def expand_env_var(v: str) -> Optional[Union[bool, int, str, list, float]]:
    if isinstance(v, str):
        return parse_arg(os.path.expandvars(v))
    else:
        return v


def expand_dict(d: Dict, expand_fn=expand_env_var, resolve_cycle_ref=True) -> Dict[str, Any]:
    expand_map = SimpleNamespace()
    pat = re.compile(r'{.+}|\$[a-zA-Z0-9_]*\b')

    def _scan(sub_d: Union[Dict, List], p):
        if isinstance(sub_d, Dict):
            for k, v in sub_d.items():
                if isinstance(v, dict):
                    p.__dict__[k] = SimpleNamespace()
                    _scan(v, p.__dict__[k])
                elif isinstance(v, list):
                    p.__dict__[k] = list()
                    _scan(v, p.__dict__[k])
                else:
                    p.__dict__[k] = v
        elif isinstance(sub_d, List):
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
                if isinstance(v, dict) or isinstance(v, list):
                    _replace(v, p.__dict__[k])
                else:
                    if isinstance(v, str) and pat.findall(v):
                        sub_d[k] = _sub(v, p)
        elif isinstance(sub_d, List):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict) or isinstance(v, list):
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


_ATTRIBUTES = {'bold': 1,
               'dark': 2,
               'underline': 4,
               'blink': 5,
               'reverse': 7,
               'concealed': 8}

_HIGHLIGHTS = {'on_grey': 40,
               'on_red': 41,
               'on_green': 42,
               'on_yellow': 43,
               'on_blue': 44,
               'on_magenta': 45,
               'on_cyan': 46,
               'on_white': 47
               }

_COLORS = {
    'grey': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37}

_RESET = '\033[0m'


def build_url_regex_pattern():
    ul = '\u00a1-\uffff'  # Unicode letters range (must not be a raw string).

    # IP patterns
    ipv4_re = r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'
    ipv6_re = r'\[[0-9a-f:.]+\]'  # (simple regex, validated later)

    # Host patterns
    hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
    # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
    domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
    tld_re = (
            r'\.'  # dot
            r'(?!-)'  # can't start with a dash
            r'(?:[a-z' + ul + '-]{2,63}'  # domain label
                              r'|xn--[a-z0-9]{1,59})'  # or punycode label
                              r'(?<!-)'  # can't end with a dash
                              r'\.?'  # may have a trailing dot
    )
    host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'

    return re.compile(
        r'^(?:[a-z0-9.+-]*)://'  # scheme is validated separately
        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
        r'(?:' + ipv4_re + '|' + ipv6_re + '|' + host_re + ')'
                                                           r'(?::\d{2,5})?'  # port
                                                           r'(?:[/?#][^\s]*)?'  # resource path
                                                           r'\Z', re.IGNORECASE)


url_pat = build_url_regex_pattern()


def is_url(text):
    return url_pat.match(text) is not None


if os.name == 'nt':
    os.system('color')


def colored(text: str, color: Optional[str] = None,
            on_color: Optional[str] = None, attrs: Union[str, list, None] = None) -> str:
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


def get_tags_from_node(node) -> List[str]:
    """Traverse the YAML by node and return all tags

    :param node: the YAML node to be traversed
    """

    def node_recurse_generator(n):
        if n.tag.startswith('!'):
            yield n.tag.lstrip('!')
        for nn in n.value:
            if isinstance(nn, tuple):
                for k in nn:
                    yield from node_recurse_generator(k)
            elif isinstance(nn, nodes.Node):
                yield from node_recurse_generator(nn)

    return list(set(list(node_recurse_generator(node))))


def kwargs2list(kwargs: Dict) -> List[str]:
    args = []
    for k, v in kwargs.items():
        k = k.replace('_', '-')
        if v is not None:
            if isinstance(v, bool):
                if v:
                    args.append(f'--{k}')
            elif isinstance(v, list):  # for nargs
                args.extend([f'--{k}', *(str(vv) for vv in v)])
            else:
                args.extend([f'--{k}', str(v)])
    return args


def get_local_config_source(path: str, to_stream: bool = False) -> Union[StringIO, TextIO, str]:
    # priority, filepath > classname > default
    import io
    from pkg_resources import resource_filename
    if hasattr(path, 'read'):
        # already a readable stream
        return path
    elif path.endswith('.yml') or path.endswith('.yaml'):
        _p = complete_path(path)
        return open(_p, encoding='utf8') if to_stream else _p
    elif path.startswith('_') and os.path.exists(
            resource_filename('jina', '/'.join(('resources', 'executors.%s.yml' % path)))):
        return resource_filename('jina', '/'.join(('resources', 'executors.%s.yml' % path)))
    elif path.startswith('!'):
        # possible YAML content
        path = path.replace('|', '\n    with: ')
        return io.StringIO(path)
    elif path.startswith('- !'):
        # possible driver YAML content, right now it is only used for debugging
        with open(resource_filename('jina', '/'.join(
                ('resources', 'executors.base.all.yml' if path.startswith('- !!') else 'executors.base.yml')))) as fp:
            _defaults = fp.read()
        path = path.replace('- !!', '- !').replace('|', '\n        with: ')  # for indent, I know, its nasty
        path = _defaults.replace('*', path)
        return io.StringIO(path)
    elif path.isidentifier():
        # possible class name
        return io.StringIO(f'!{path}')
    else:
        raise FileNotFoundError(f'{path} can not be resolved, it should be a readable stream,'
                                ' or a valid file path, or a supported class name.')


def is_valid_local_config_source(path: str) -> bool:
    try:
        get_local_config_source(path)
        return True
    except FileNotFoundError:
        return False


def get_parsed_args(kwargs: Dict[str, Union[str, int, bool]],
                    parser: ArgumentParser, parser_name: str = None
                    ) -> Tuple[List[str], Namespace, List[Any]]:
    args = kwargs2list(kwargs)
    try:
        p_args, unknown_args = parser.parse_known_args(args)
        if unknown_args:
            from .logging import default_logger
            default_logger.warning(
                f'parser {parser_name} can not '
                f'recognize the following args: {unknown_args}, '
                f'they are ignored. if you are using them from a global args (e.g. Flow), '
                f'then please ignore this message')
    except SystemExit:
        raise ValueError('bad arguments "%s" with parser %r, '
                         'you may want to double check your args ' % (args, parser))
    return args, p_args, unknown_args


def get_non_defaults_args(args: Namespace, parser: ArgumentParser, taboo: Set[Optional[str]] = None) -> Dict:
    if taboo is None:
        taboo = set()
    non_defaults = {}
    _defaults = vars(parser.parse_args([]))
    for k, v in vars(args).items():
        if k in _defaults and k not in taboo and _defaults[k] != v:
            non_defaults[k] = v
    return non_defaults


def get_full_version() -> Optional[Tuple[Dict, Dict]]:
    from . import __version__, __proto_version__, __jina_env__
    from google.protobuf.internal import api_implementation
    import os, zmq, numpy, google.protobuf, grpc, ruamel.yaml
    from grpc import _grpcio_metadata
    from pkg_resources import resource_filename
    import platform
    from .logging import default_logger
    try:

        info = {'jina': __version__,
                'jina-proto': __proto_version__,
                'jina-vcs-tag': os.environ.get('JINA_VCS_VERSION', '(unset)'),
                'libzmq': zmq.zmq_version(),
                'pyzmq': numpy.__version__,
                'protobuf': google.protobuf.__version__,
                'proto-backend': api_implementation._default_implementation_type,
                'grpcio': getattr(grpc, '__version__', _grpcio_metadata.__version__),
                'ruamel.yaml': ruamel.yaml.__version__,
                'python': platform.python_version(),
                'platform': platform.system(),
                'platform-release': platform.release(),
                'platform-version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'jina-resources': resource_filename('jina', 'resources')
                }
        env_info = {k: os.getenv(k, '(unset)') for k in __jina_env__}
        full_version = info, env_info
    except Exception as e:
        default_logger.error(str(e))
        full_version = None

    return full_version


def format_full_version_info(info: Dict, env_info: Dict) -> str:
    version_info = '\n'.join(f'{k:30s}{v}' for k, v in info.items())
    env_info = '\n'.join(f'{k:30s}{v}' for k, v in env_info.items())
    return version_info + '\n' + env_info


def use_uvloop():
    if 'JINA_DISABLE_UVLOOP' not in os.environ:
        try:
            import asyncio
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except (ModuleNotFoundError, ImportError):
            from .logging import default_logger
            default_logger.error(
                'Since v0.3.6 jina uses uvloop to manage events and sockets, it often yields 20% speedup'
                'you did not install uvloop. Try "pip install uvloop"')


def show_ioloop_backend(loop: Optional['Loop'] = None) -> None:
    if loop is None:
        import asyncio
        loop = asyncio.get_event_loop()
    from .logging import default_logger
    default_logger.info(f'using {loop.__class__} as event loop')


def rsetattr(obj, attr: str, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr: str, *args):
    def _getattr(obj, attr):
        if isinstance(obj, dict):
            return obj.get(attr, None)
        else:
            return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))


class cached_property:
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        cached_value = obj.__dict__.get(f'CACHED_{self.func.__name__}', None)
        if cached_value is not None:
            return cached_value

        value = obj.__dict__[f'CACHED_{self.func.__name__}'] = self.func(obj)
        return value


def get_now_timestamp():
    now = datetime.now()
    return int(datetime.timestamp(now))


def complete_path(path: str) -> str:
    import inspect
    _p = None

    if os.path.exists(path):
        # this checks both abs and relative paths already
        _p = path
    else:
        search_paths = []
        frame = inspect.currentframe()

        # iterates on whoever calls me
        while frame:
            search_paths.append(os.path.dirname(inspect.getfile(frame)))
            frame = frame.f_back
        search_paths += os.environ['PATH'].split(os.pathsep)

        # not in local path, search within all search paths
        for p in search_paths:
            _p = os.path.join(p, path)
            if os.path.exists(_p):
                break
    if _p:
        return _p
    else:
        raise FileNotFoundError(f'can not find {path}')


def get_readable_time(*args, **kwargs):
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
