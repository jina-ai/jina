from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.composite import CompositeServer

__all__ = ['CompositeGateway']


class CompositeGateway(CompositeServer, BaseGateway):
    pass
