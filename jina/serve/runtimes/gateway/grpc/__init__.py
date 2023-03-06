from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.grpc import GRPCServer

__all__ = ['GRPCGateway']


class GRPCGateway(GRPCServer, BaseGateway):
    pass

