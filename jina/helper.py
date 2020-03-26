import os
import random
import re
import string
import sys
import threading
import time
from itertools import islice
from types import SimpleNamespace
from typing import Iterator, Any, Union, List, Dict

import numpy as np
from ruamel.yaml import YAML, nodes

from . import JINA_GLOBAL

__all__ = ['batch_iterator', 'yaml',
           'load_contrib_module',
           'parse_arg',
           'PathImporter', 'random_port', 'random_identity', 'expand_env_var',
           'colored', 'kwargs2list', 'valid_yaml_path']


def print_load_table(load_stat):
    from .logging import default_logger

    load_table = []
    for k, v in load_stat.items():
        for cls_name, import_stat, err_reason in v:
            load_table.append('%-5s %-25s %-40s %s' % (
                colored('✓', 'green') if import_stat else colored('✗', 'red'),
                cls_name if cls_name else colored('Module load error', 'red'), k, str(err_reason)))
    if load_table:
        load_table = ['', '%-5s %-25s %-40s %-s' % ('Load', 'Class', 'Module', 'Reason'),
                      '%-5s %-25s %-40s %-s' % ('-' * 5, '-' * 25, '-' * 40, '-' * 10)] + load_table
        default_logger.info('\n'.join(load_table))


def call_obj_fn(obj, fn: str):
    if obj is not None and hasattr(obj, fn):
        getattr(obj, fn)()


def touch_dir(base_dir: str) -> None:
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)


def batch_iterator(data: Union[Iterator[Any], List[Any], np.ndarray], batch_size: int, axis: int = 0) -> Iterator[Any]:
    if not batch_size or batch_size <= 0:
        yield data
        return
    if isinstance(data, np.ndarray):
        if batch_size >= data.shape[axis]:
            yield data
            return
        for _ in range(0, data.shape[axis], batch_size):
            start = _
            end = min(len(data), _ + batch_size)
            yield np.take(data, range(start, end), axis, mode='clip')
    elif hasattr(data, '__len__'):
        if batch_size >= len(data):
            yield data
            return
        for _ in range(0, len(data), batch_size):
            yield data[_:_ + batch_size]
    elif isinstance(data, Iterator):
        # as iterator, there is no way to know the length of it
        while True:
            chunk = tuple(islice(data, batch_size))
            if not chunk:
                return
            yield chunk
    else:
        raise TypeError('unsupported type: %s' % type(data))


def _get_yaml():
    y = YAML(typ='safe')
    y.default_flow_style = False
    return y


def parse_arg(v: str):
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


def countdown(t: int, logger=None, reason: str = 'I am blocking this thread'):
    if not logger:
        sys.stdout.write('\n')
        sys.stdout.flush()
    while t > 0:
        t -= 1
        msg = '%ss left: %s' % (colored('%3d' % t, 'yellow'), reason)
        if logger:
            logger.info(msg)
        else:
            sys.stdout.write('\r%s' % msg)
            sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write('\n')
    sys.stdout.flush()


def load_contrib_module():
    if 'JINA_CONTRIB_MODULE_IS_LOADING' not in os.environ:

        contrib = os.getenv('JINA_CONTRIB_MODULE')
        os.environ['JINA_CONTRIB_MODULE_IS_LOADING'] = 'true'

        modules = []

        if contrib:
            from .logging import default_logger
            default_logger.info(
                'find a value in $JINA_CONTRIB_MODULE=%s, will load them as external modules' % contrib)
            for p in contrib.split(','):
                m = PathImporter.add_modules(p)
                modules.append(m)
                default_logger.info('successfully registered %s class, you can now use it via yaml.' % m)
        return modules


class PathImporter:

    @staticmethod
    def _get_module_name(absolute_path):
        module_name = os.path.basename(absolute_path)
        module_name = module_name.replace('.py', '')
        return module_name

    @staticmethod
    def add_modules(*paths):
        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError('cannot import module from %s, file not exist', p)
            module, spec = PathImporter._path_import(p)
        return module

    @staticmethod
    def _path_import(absolute_path):
        import importlib.util
        module_name = PathImporter._get_module_name(absolute_path)
        spec = importlib.util.spec_from_file_location(module_name, absolute_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[spec.name] = module
        return module, spec


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
    return '-'.join(random.choice(_random_names[j]) for j in range(2))


def random_port() -> int:
    from contextlib import closing
    import socket
    import threading
    with threading.Lock():
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]


def get_registered_ports(stack_id: int = JINA_GLOBAL.stack.id):
    config_path = os.environ.get('JINA_STACK_CONFIG', '.jina-stack.yml')
    _all = {}
    _ports = set()
    if os.path.exists(config_path):
        with open(config_path) as fp:
            _all = yaml.load(fp)
        if _all and 'stacks' in _all:
            for s in _all['stacks']:
                if (stack_id is not None and s['id'] == stack_id) or stack_id is None:
                    _ports.update(s['ports'])
    return list(_ports)


def deregister_all_ports(stack_id: int = JINA_GLOBAL.stack.id):
    config_path = os.environ.get('JINA_STACK_CONFIG', '.jina-stack.yml')
    _all = {'stacks': []}
    if os.path.exists(config_path):
        with open(config_path) as fp:
            _all = yaml.load(fp)
    if 'stacks' in _all:
        for s in _all['stacks']:
            if s['id'] == stack_id:
                _all['stacks'].remove(s)
                break
    with open(config_path, 'w') as fp:
        yaml.dump(_all, fp)


def register_port(port: int, stack_id: int = JINA_GLOBAL.stack.id):
    config_path = os.environ.get('JINA_STACK_CONFIG', '.jina-stack.yml')
    _all = None
    if os.path.exists(config_path):
        with open(config_path) as fp:
            _all = yaml.load(fp)
    if not _all or 'stacks' not in _all:
        _all = {'stacks': []}
    already_in = False
    from jina import JINA_GLOBAL
    stack_id = stack_id or JINA_GLOBAL.stack.id
    for s in _all['stacks']:
        if s['id'] == stack_id:
            s['ports'] = list(set(s['ports'] + [port]))
            already_in = True
            break
    if not already_in:
        r = {
            'id': stack_id,
            'ports': [port]
        }
        _all['stacks'].append(r)
    with open(config_path, 'w') as fp:
        yaml.dump(_all, fp)


def random_identity() -> str:
    return '%s-%s-%s' % (os.getpid(), threading.get_ident(), ''.join(random.choices(string.ascii_lowercase, k=5)))


yaml = _get_yaml()


def expand_env_var(v: str) -> str:
    if isinstance(v, str):
        return parse_arg(os.path.expandvars(v))
    else:
        return v


def expand_dict(d: Dict) -> Dict[str, Any]:
    expand_map = SimpleNamespace()

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
                    if isinstance(v, str) and (re.match(r'{.*?}', v) or re.match(r'\$.*\b', v)):
                        sub_d[k] = expand_env_var(v.format(root=expand_map, this=p))
        elif isinstance(sub_d, List):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict) or isinstance(v, list):
                    _replace(v, p[idx])
                else:
                    if isinstance(v, str) and (re.match(r'{.*?}', v) or re.match(r'\$.*\b', v)):
                        sub_d[idx] = expand_env_var(v.format(root=expand_map, this=p))

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

if os.name == 'nt':
    os.system('color')


def colored(text, color=None, on_color=None, attrs=None):
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


def kwargs2list(kwargs: Dict):
    args = []
    for k, v in kwargs.items():
        if v is not None:
            if isinstance(v, bool):
                if v:
                    args.append('--%s' % k)
            elif isinstance(v, list):  # for nargs
                args.extend(['--%s' % k, *(str(vv) for vv in v)])
            else:
                args.extend(['--%s' % k, str(v)])
    return args


def valid_yaml_path(path: str, to_stream: bool = False):
    # priority, filepath > classname > default
    import io
    if hasattr(path, 'read'):
        # already a readable stream
        return path
    elif os.path.exists(path):
        if to_stream:
            return open(path, encoding='utf8')
        else:
            return path
    elif path.lower() in {'route', 'merge', 'clear', 'logroute'}:
        from pkg_resources import resource_filename
        return resource_filename('jina', '/'.join(('resources', 'executors.%s.yml' % path)))
    elif path.startswith('!'):
        # possible YAML content
        return io.StringIO(path)
    elif path.isidentifier():
        # possible class name
        return io.StringIO('!%s' % path)
    else:
        raise FileNotFoundError('%s can not be resolved, it should be a readable stream,'
                                ' or a valid file path, or a supported class name.' % path)
