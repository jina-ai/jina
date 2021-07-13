from .peas import _PeaClient


class _PodClient(_PeaClient):

    kind = 'pod'
    endpoint = '/pods'
