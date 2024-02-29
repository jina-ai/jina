from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.http import FastAPIBaseServer

__all__ = ['FastAPIBaseGateway']


class FastAPIBaseGateway(FastAPIBaseServer, BaseGateway):
    """
    :class:`FastAPIBaseGateway` is a FastAPIBaseServer that can be loaded from YAML as any other Gateway
    """

    pass
