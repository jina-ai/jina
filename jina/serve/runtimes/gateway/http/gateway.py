from jina.helper import extend_rest_interface

from ....gateway import BaseGateway
from . import get_fastapi_app


class HTTPGateway(BaseGateway):
    """HTTP Gateway implementation"""

    def get_app(self):
        """
        initialize and return ASGI application
        :return: ASGI Application
        """
        return extend_rest_interface(
            get_fastapi_app(
                streamer=self.streamer,
                args=self.args,
                logger=self.logger,
            )
        )
