from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.http import FastAPIBaseServer

__all__ = ['HTTPGateway', 'FastAPIBaseGateway']


class FastAPIBaseGateway(FastAPIBaseServer, BaseGateway):
    """
    :class:`FastAPIBaseGateway` is a FastAPIBaseServer that can be loaded from YAML as any other Gateway
    """
    pass


class HTTPGateway(FastAPIBaseGateway):
    """
    :class:`HTTPGateway` is a FastAPIBaseGateway that uses the default FastAPI app
    """
    @property
    def app(self):
        return self._request_handler._http_fastapi_default_app(title=self.title,
                                                               description=self.description,
                                                               no_crud_endpoints=self.no_crud_endpoints,
                                                               no_debug_endpoints=self.no_debug_endpoints,
                                                               expose_endpoints=self.expose_endpoints,
                                                               expose_graphql_endpoint=self.expose_graphql_endpoint,
                                                               tracing=self.tracing,
                                                               tracer_provider=self.tracer_provider,
                                                               cors=self.cors)
