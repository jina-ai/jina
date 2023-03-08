from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.composite import CompositeServer

__all__ = ['CompositeGateway']


class CompositeGateway(CompositeServer, BaseGateway):
    """
    :class:`CompositeGateway` is a CompositeServer that can be loaded from YAML as any other Gateway
    """
    pass
