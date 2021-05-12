import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Union

from daemon import jinad_args


def get_workspace_path(workspace_id: Union[uuid.UUID, str], *args):
    """get the path to the ws

    :param workspace_id: the id of the ws
    :param args: paths to join
    :return: the full path
    """
    return os.path.join(
        jinad_args.workspace, str(workspace_id), *[str(a) for a in args]
    )


@contextmanager
def jina_workspace(workspace_id: uuid.UUID):
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
