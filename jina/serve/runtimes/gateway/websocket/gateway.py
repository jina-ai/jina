from jina.helper import extend_rest_interface

from ....gateway import BaseGateway
from . import get_fastapi_app


class WebSocketGateway(BaseGateway):
    """WebSocket Gateway implementation"""

    def get_app(self):
        """
        Initialize and return ASGI app
        :return: ASGI app
        """
        return extend_rest_interface(
            get_fastapi_app(
                streamer=self.streamer,
                args=self.args,
                logger=self.logger,
            )
        )
