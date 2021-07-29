from .peas import AsyncPeaClient
from .mixin import AsyncToSyncMixin


class AsyncPodClient(AsyncPeaClient):
    """Async Client to create/update/delete Peods on remote JinaD"""

    _kind = 'pod'
    _endpoint = '/pods'


class PodClient(AsyncToSyncMixin, AsyncPodClient):
    """Client to create/update/delete Pods on remote JinaD"""
