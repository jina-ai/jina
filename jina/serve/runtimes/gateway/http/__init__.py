from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.http import FastAPIBaseServer

__all__ = ['HTTPGateway', 'FastAPIBaseGateway']


class FastAPIBaseGateway(FastAPIBaseServer, BaseGateway):
    pass


class HTTPGateway(FastAPIBaseGateway):
    @property
    def app(self):
        return self._request_handler._http_fastapi_default_app()
