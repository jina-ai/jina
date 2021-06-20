import os
import re
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from .models import DaemonID

EXCEPTS_REGEX = r'\b(error|failed|FAILURES)\b'


class classproperty:
    """Helper class to read property inside a classmethod"""

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def id_cleaner(docker_id: str, prefix: str = 'sha256:') -> str:
    """Get 1st 10 characters in id created by docker

    :param docker_id: id of docker object
    :param prefix: defaults to 'sha256:'
    :return: shorter id
    """
    return docker_id[docker_id.startswith(prefix) and len(prefix) :][:10]


def get_workspace_path(workspace_id: 'DaemonID', *args):
    """get the path to the ws

    :param workspace_id: the id of the ws
    :param args: paths to join
    :return: the full path
    """
    from . import __root_workspace__

    return os.path.join(__root_workspace__, workspace_id, *[str(a) for a in args])


def is_error_message(s) -> bool:
    """
    Check if the string matches an exception regex.
    :param s: the string to check
    :return: whether or not it matches
    """
    return re.search(EXCEPTS_REGEX, s, re.IGNORECASE | re.UNICODE) is not None


def get_log_file_path(log_id: 'DaemonID') -> Tuple[str, 'DaemonID']:
    """Get logfile path from id

    :param log_id: DaemonID in the store
    :return: logfile path, workspace_id for log_id
    """
    from .models.enums import IDLiterals
    from .stores import get_store_from_id

    if IDLiterals.JWORKSPACE == log_id.jtype:
        workspace_id = log_id
        filepath = get_workspace_path(log_id, 'logs', 'logging.log')
    else:
        workspace_id = get_store_from_id(log_id)[log_id].workspace_id
        filepath = get_workspace_path(workspace_id, 'logs', log_id, 'logging.log')
    return filepath, workspace_id
