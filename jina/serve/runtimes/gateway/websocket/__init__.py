from jina.serve.runtimes.gateway.gateway import BaseGateway
from jina.serve.runtimes.servers.websocket import WebSocketServer

__all__ = ['WebSocketGateway']


class WebSocketGateway(WebSocketServer, BaseGateway):
    @property
    def app(self):
        return self._request_handler._websocket_fastapi_default_app()
