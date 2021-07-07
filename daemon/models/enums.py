import os
from enum import Enum
from typing import List

from ..helper import classproperty


class DaemonEnum(str, Enum):
    """Base class of Enum in JinaD"""

    @classproperty
    def values(cls) -> List:
        """Get all values in Enum

        :return: Get all values in Enum
        """
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

    @classproperty
    def default(cls) -> str:
        """Get default value for DaemonBuild

        .. note::
            set env var `JINA_DAEMON_BUILD` to `DEVEL` if you're working on dev mode

        :return: default value for DaemonBuild"""
        return cls.DEVEL if os.getenv('JINA_DAEMON_BUILD') == 'DEVEL' else cls.DEFAULT


class PythonVersion(DaemonEnum):
    """Enum representing python versions allowed in .jinad file"""

    PY37 = '3.7'
    PY38 = '3.8'
    PY39 = '3.9'

    @classproperty
    def default(cls) -> str:
        """Get default value for PythonVersion

        :return: default value for PythonVersion"""
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

    ROLLING_UPDATE = 'rolling_update'
