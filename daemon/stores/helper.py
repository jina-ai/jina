import os
from pathlib import Path
from contextlib import contextmanager

from ..models import DaemonID
from .. import __root_workspace__


def get_workspace_path(workspace_id: DaemonID, *args):
    """get the path to the ws

    :param workspace_id: the id of the ws
    :param args: paths to join
    :return: the full path
    """
    return os.path.join(
        __root_workspace__, workspace_id, *[str(a) for a in args]
    )

@contextmanager
def jina_workspace(workspace_id: DaemonID):
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


# from pydantic import FilePath
# from pathlib import Path
# try:
#     FilePath.validate(Path(''))
# except Exception as e:
#     print(repr(e))
