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


class DaemonBuild(DaemonEnum):
    DEVEL = 'devel'
    DEFAULT = 'default'
    CPU = 'default'
    GPU = 'gpu'

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
