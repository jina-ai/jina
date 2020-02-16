import os
import random
import string
import sys
import threading
import time
from itertools import islice
from typing import Iterator, Any, Union, List

import numpy as np
from ruamel.yaml import YAML
from termcolor import colored

__all__ = ['batch_iterator', 'yaml',
           'load_contrib_module',
           'parse_arg',
           'PathImporter', 'random_port', 'random_identity', 'expand_env_var']


def print_load_table(load_stat):
    from jina.logging import default_logger

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
    if not os.getenv('JINA_CONTRIB_MODULE_IS_LOADING'):

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


def random_port(port: int = None) -> int:
    if not port or int(port) <= 0:
        import random
        min_port, max_port = 49152, 65536
        return random.randrange(min_port, max_port)
    else:
        return int(port)


def random_identity() -> str:
    return '%s-%s-%s' % (os.getpid(), threading.get_ident(), ''.join(random.choices(string.ascii_lowercase, k=5)))


yaml = _get_yaml()


def expand_env_var(v: str) -> str:
    if isinstance(v, str):
        return parse_arg(os.path.expandvars(v))
    else:
        return v