from enum import Enum
from ..helper import classproperty


class DaemonEnum(str, Enum):
    @classproperty
    def values(cls):
        return list(map(lambda c: c.value, cls))


class IDLiterals(DaemonEnum):
    JPOD = 'jpod'
    JPEA = 'jpea'
    JFLOW = 'jflow'
    JNETWORK = 'jnetwork'
    JWORKSPACE = 'jworkspace'


class WorkspaceState(DaemonEnum):
    PENDING = 'PENDING'
    CREATING = 'CREATING'
    UPDATING = 'UPDATING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'
    DELETING = 'DELETING'


class DaemonBuild(DaemonEnum):
    DEVEL = 'devel'
    DEFAULT = 'default'
    CPU = 'default'
    GPU = 'gpu'

    # TODO (Deepankar): remove this once default becomes default
    @classproperty
    def default(cls):
        return cls.DEVEL


class PythonVersion(DaemonEnum):
    PY37 = '3.7'
    PY38 = '3.8'
    PY39 = '3.9'

    @classproperty
    def default(cls):
        return cls.PY38


class PartialDaemonModes(DaemonEnum):
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
