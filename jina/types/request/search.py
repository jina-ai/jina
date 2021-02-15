from . import Request
from .mixin import *


class SearchRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    """Search request class."""

    pass
