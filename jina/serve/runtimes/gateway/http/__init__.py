from jina.serve.runtimes.gateway.http.fastapi import FastAPIBaseGateway # keep import here for backwards compatibility
from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.http import HTTPServer

__all__ = ['HTTPGateway']


class HTTPGateway(HTTPServer, BaseGateway):
    """
    :class:`HTTPGateway` is a FastAPIBaseGateway that uses the default FastAPI app
    """
    pass


class HTTPExecutorGateway(HTTPServer, BaseGateway):
    """
    :class:`HTTPGateway` is a FastAPIBaseGateway that uses the default FastAPI app
    """
    @property
    def app(self):
        """Get the default base API app for Server
        :return: Return a FastAPI app for the default HTTPGateway
        """
        return self._request_handler._http_fastapi_executor_app()
