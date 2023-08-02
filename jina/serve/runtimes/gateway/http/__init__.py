from jina.serve.runtimes.gateway.http.fastapi import FastAPIBaseGateway # keep import here for backwards compatibility
from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.http import HTTPServer

__all__ = ['HTTPGateway']


class HTTPGateway(HTTPServer, BaseGateway):
    """
    :class:`HTTPGateway` is a FastAPIBaseGateway that uses the default FastAPI app
    """
    pass
