from .base import BaseClient
from .peas import AsyncPeaClient


class AsyncPodClient(AsyncPeaClient):
    """Async Client to create/update/delete Peods on remote JinaD"""

    _kind = 'pod'
    _endpoint = '/pods'


class PodClient(BaseClient, AsyncPodClient):
    """Client to create/update/delete Pods on remote JinaD"""
