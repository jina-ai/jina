from .peas import PeaStore


class PodStore(PeaStore):
    """A Store of Pods spawned as Containers by Daemon"""

    _kind = 'pod'
