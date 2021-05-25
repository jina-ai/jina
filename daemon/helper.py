import os
import random
from pathlib import Path
from typing import TYPE_CHECKING
from contextlib import contextmanager

from . import __root_workspace__

if TYPE_CHECKING:
    from .models import DaemonID


class classproperty:
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def id_cleaner(docker_id: str, prefix: str = 'sha256:') -> str:
    return docker_id[docker_id.startswith(prefix) and len(prefix) :][:10]


def get_workspace_path(workspace_id: 'DaemonID', *args):
    """get the path to the ws

    :param workspace_id: the id of the ws
    :param args: paths to join
    :return: the full path
    """
    return os.path.join(__root_workspace__, workspace_id, *[str(a) for a in args])


def range_conflict(range_a_min, range_b_min, count):
    return (
        len(
            range(
                max(range_a_min, range_b_min),
                min(range_a_min + count, range_b_min + count) + 1,
            )
        )
        != 0
    )


def random_port_range(port_min: int = 49153, port_max: int = 65535, count: int = 100):
    from .stores import workspace_store

    for _ in range(10):
        _jina_random_port_min = random.randint(port_min, port_max)
        for i in workspace_store.values():
            if 'ports' in i['metadata'] and 'min' in i['metadata']['ports']:
                _min = i['metadata']['ports']['min']
                if range_conflict(_jina_random_port_min, _min, count):
                    break
        else:
            return _jina_random_port_min, _jina_random_port_min + count


def port_fields_from_pydantic(model):
    return {
        i: getattr(model, i)
        for i in model.__fields__
        if 'port' in i and i != 'port_expose'
    }


@contextmanager
def jina_workspace(workspace_id: 'DaemonID'):
    """
    Change the current working dir to ``path`` in a context and set it back to the original one when leaves the context.

    :param workspace_id: the id of the workspace
    :yields: the workspace as str
    """
    old_dir = os.getcwd()
    old_var = os.environ.get('JINA_LOG_WORKSPACE', None)
    _workdir = get_workspace_path(workspace_id)
    Path(_workdir).mkdir(parents=True, exist_ok=True)
    os.environ['JINA_LOG_WORKSPACE'] = _workdir
    os.chdir(_workdir)
    try:
        yield _workdir
    finally:
        os.chdir(old_dir)
        if old_var:
            os.environ['JINA_LOG_WORKSPACE'] = old_var
        else:
            os.environ.pop('JINA_LOG_WORKSPACE')
