from enum import Enum

from jina.enums import RemoteWorkspaceState as WorkspaceState
from ..helper import classproperty


class DaemonEnum(str, Enum):
    """Base class of Enum in JinaD"""

    @classproperty
    def values(cls):
        """Get all values in Enum"""
        return list(map(lambda c: c.value, cls))


class IDLiterals(DaemonEnum):
    """Enum representing all values allowed in DaemonID"""

    JPOD = 'jpod'
    JPEA = 'jpea'
    JFLOW = 'jflow'
    JNETWORK = 'jnetwork'
    JWORKSPACE = 'jworkspace'


class DaemonBuild(DaemonEnum):
    """Enum representing build value passed in .jinad file"""

    DEVEL = 'devel'
    DEFAULT = 'default'
    CPU = 'default'
    GPU = 'gpu'

    # TODO (Deepankar): remove this once default becomes default
    @classproperty
    def default(cls):
        return cls.DEVEL


class PythonVersion(DaemonEnum):
    """Enum representing python versions allowed in .jinad file"""

    PY37 = '3.7'
    PY38 = '3.8'
    PY39 = '3.9'

    @classproperty
    def default(cls):
        return cls.PY38


class PartialDaemonModes(DaemonEnum):
    """Enum representing partial daemon modes"""

    PEA = 'pea'
    POD = 'pod'
    FLOW = 'flow'


class UpdateOperation(DaemonEnum):
    """
    Represents the type of operation to perform in the update
    We consider these an `update` operation since they **change** the underlying state
    """

    DUMP = 'dump'
    ROLLING_UPDATE = 'rolling_update'
