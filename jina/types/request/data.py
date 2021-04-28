from . import Request
from .mixin import *


class DataRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    """Data request class."""

    @property
    def endpoint(self) -> str:
        """Get the command."""
        return self.body.endpoint

    @endpoint.setter
    def endpoint(self, val: str):
        """Get the command."""
        self.body.endpoint = val
