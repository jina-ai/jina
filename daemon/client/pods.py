from .peas import AsyncPeaClient, PeaClient


class AsyncPodClient(AsyncPeaClient):

    kind = 'pod'
    endpoint = '/pods'


class PodClient(AsyncPodClient, PeaClient):
    """[summary]"""
